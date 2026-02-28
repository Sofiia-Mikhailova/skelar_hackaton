# 🇺🇦 AI Support Quality Analysis Pipeline / 🇬🇧 AI Support Quality Analysis Pipeline

## 🇺🇦 Огляд проєкту

Цей репозиторій містить професійну pipeline-систему для генерації синтетичних датасетів клієнтської підтримки з високою варіативністю та проведення високоточного аудиту якості за допомогою великих мовних моделей (LLM).

Система розроблена для вирішення кількох ключових проблем:

- Прихована незадоволеність — коли клієнт формально дякує, але його питання так і не вирішили
- Помилки агента — неправильна інформація, ігнорування запиту, грубий тон
- Складні сценарії — проблеми з оплатою, технічні збої, доступ до акаунту, питання по тарифу, повернення коштів
- Оцінка якості роботи агента - чи вирішено проблему, як саме вирішено/не вирішено проблему, як швидко вирішено проблему (трекінг часу)

Для генерації використовується легша модель `llama-3.1-8b-instant`, а для аналізу — потужніша `llama-3.3-70b-versatile`. Вибір і конфігурація обох моделей централізовані в `llm_client.py`.
У папці `utils/` міститься скрипт для бенчмаркінгу, який валідує результати аналізатора шляхом багаторазових запусків на одних і тих самих діалогах. У випадках розбіжностей проводилась ручна перевірка — незалежний аналіз чату людиною давав той самий результат, що й аналізатор. Це підтверджує надійність та точність аналізатора.

### Структура проєкту

Проєкт побудований за модульною, production-ready архітектурою:

- **`src/`** — Основна логіка програми
  - `generate.py` — генерує синтетичні діалоги
  - `analyze.py` — перевіряє якість розмов (детерміновано)
  - `llm_client.py` — клієнт для роботи з Groq API, повертає відповіді у форматі JSON
- **`data/`** — тут зберігаються датасети та результати аналізу
- **`utils/`** — допоміжні скрипти для тестування, бенчмаркінгу та перевірки стабільності результатів
- **`.env.example`** — шаблон для збереження API-ключів

## Основна логіка та Prompt Engineering

### 1. Генерація з високою варіативністю та реалістичністю (`generate.py`)

Щоб згенерувати реалістичні та різноманітні діалоги, генератор використовує `llama-3.1-8b-instant` із **temperature = 0.8** для досягнення максимальної різноманітності.

**Логіка людської поведінки, яку враховує генератор:**

- **Природний ритм повідомлень:** клієнт надсилає привітання та проблему у **2–3 окремих повідомленнях** (наприклад, «hi» → «i have a problem»), агент аналізує ці повідомлення як одну думку.
- **Мовна реалістичність:** використання сленгу, скорочень (thx, ok then, noted), відсутність великих літер, в той час як агент зберігає професійний профіль.
- **Емоційний «шум»:** періодичне використання **ALL CAPS**, граматичних помилок або надмірної пунктуації.
- **Різні сценарії завершення:** не всі діалоги завершуються вирішенням. Генеруються сценарії «Customer Silent», де клієнт перестає відповідати, агент очікує повідомлення деякий час, після чого повідомляє про закриття діалогу.

### 2. Аналіз за принципом «Спочатку результат» (`analyze.py`)

Аналізатор використовує `llama-3.3-70b-versatile` з **temperature = 0.0** для забезпечення детермінованості.

**Ключові аналітичні принципи:**

- **Результат важливіший за тон:** Тон клієнта ≠ задоволення. Агресивний клієнт, чию проблему вирішено, позначається як `satisfied`, тоді як ввічливий клієнт із невирішеним питанням — як `unsatisfied`.
- Визначення intent звернення: Аналізатор автоматично класифікує тему кожного діалогу:
   - `tech_error`
   - `account_access`
   - `payment_issue`
   - `pricing_plan`
   - `refund_request`
   - `other`
- **Виявлення прихованого невдоволення:** Якщо користувач каже «thanks», але основний запит не виконано — система позначає взаємодію як `hidden_dissatisfaction`.
- **Таксономія помилок агента:** Агент перевіряється на конкретні помилки:
  - `wrong_customer_name`
  - `ignored_question`
  - `security_violation`
  - `incorrect_info`
  - `no_resolution`
  - `unnecesary_escalation`
  - `rude_tone`

Логіка людської поведінки та агента враховується як в генераторі, так і в аналізаторі.

## Технічна реалізація

### 1. Детермінованість та узгодженість

Фаза аналізу суворо детермінована відповідно до вимог:

- **Greedy decoding:** `temperature = 0.0`
- **Примусовий JSON-режим:** гарантує структурований машинозчитуваний результат
- **Стабільність:** реалізовано exponential backoff для обробки помилок `429 Resource Exhausted` під час масової обробки

Детермінованість була перевірена практично: ми запускали аналізатор декілька разів на одних і тих самих випадково обраних діалогах. За результатами тестування виявлено лише 1 розбіжність на 20 чатів, що відповідає **~95% стабільності** результатів — високий показник для LLM-системи в production-середовищі.

### 2. Шкала оцінювання якості (1–5)

| Бал | Рівень | Критерії |
|-----|--------|----------|
| **5** | **Відмінно** | Ідеальне виконання: швидко, ввічливо, всі питання вирішено, ім'я клієнта використано правильно. |
| **4** | **Добре** | Проблему вирішено, сервіс якісний, але пропущено незначну деталь. |
| **3** | **Середньо** | Проблему вирішено частково, або тон роботизований / пропущено питання. |
| **2** | **Погано** | Серйозні помилки: неправильна інформація, ігнорування ключового питання, неправильне ім'я. |
| **1** | **Провал** | Критична помилка: грубий тон, порушення безпеки (запит пароля), відсутність допомоги. |


## Встановлення та використання

### 1. Налаштування середовища

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Налаштування API

Створіть файл `.env` у корені проєкту:

```env
GROQ_API_KEY=your_actual_api_key_here
```
Для доступу до великих мовних моделей ми використали GROQ-ключ

### 3. Запуск pipeline

```bash
# Крок 1: Генерація синтетичних чатів
python src/generate.py

# Крок 2: Детермінований аудит
python src/analyze.py
```
---
---

## 🇬🇧 Project Overview

This repository contains a professional-grade pipeline for generating high-variance synthetic customer support datasets and performing high-precision quality audits using Large Language Models (LLMs).

The system is designed to tackle several key support challenges:

- **Hidden dissatisfaction** — when a customer formally says "thanks" but their issue was never actually resolved
- **Agent mistakes** — wrong information, ignored requests, rude tone
- **Complex scenarios** — payment issues, technical errors, account access, billing questions, refunds
- **Agent performance evaluation** — whether the issue was resolved, how it was or wasn't resolved, and how quickly it was resolved (time tracking)

For generation, the lighter `llama-3.1-8b-instant` model is used, while the more powerful `llama-3.3-70b-versatile` handles analysis. The selection and configuration of both models are centralized in `llm_client.py`.

The `utils/` folder contains a benchmarking script that validates the analyzer's results through repeated runs on the same dialogues. In cases of discrepancy, manual review was conducted — independent human analysis of the chat consistently reached the same conclusion as the analyzer, confirming the analyzer's reliability and accuracy.

---

## Project Structure

The project follows a modular, production-ready architecture:

- **`src/`** – Core application logic
  - `generate.py` – Synthetic dialogue generation engine
  - `analyze.py` – Deterministic quality auditing engine
  - `llm_client.py` – Centralized Groq API client with structured JSON handling
- **`data/`** – Storage for clean datasets and analysis results
- **`utils/`** – Helper scripts for benchmarking, reference data, and determinism testing
- **`.env.example`** – Template for secure API key management

---

## Core Logic & Prompt Engineering

### 1. High-Variance Generation (`generate.py`)

To generate realistic and diverse dialogues, the generator uses `llama-3.1-8b-instant` with **temperature = 0.8** to maximize diversity.

**Human-Centric Diversity Logic:**

- **Natural message pacing:** The customer sends greetings and the actual problem across **2–3 separate messages** (e.g., "hi" → "i have a problem"), while the agent treats them as a single thought.
- **Linguistic realism:** Incorporates slang, short abbreviations (thx, ok then, noted), and missing capitalization, while the agent maintains a professional tone.
- **Emotional noise:** Occasionally uses **ALL CAPS**, grammar mistakes, or excessive punctuation to simulate frustration.
- **Varied chat endings:** Not all chats end with resolution. "Customer Silent" scenarios simulate inactivity — the agent waits for a response and eventually notifies the customer that the chat will be closed.

---

### 2. Resolution-First Analysis (`analyze.py`)

The analyzer uses `llama-3.3-70b-versatile` with **temperature = 0.0** to ensure deterministic audits.

**Key Analytical Pillars:**

- **Outcome over sentiment:** Customer tone ≠ satisfaction. An aggressive customer whose issue is resolved is marked `satisfied`, while a polite customer with an unresolved issue is marked `unsatisfied`.
- **Intent classification:** The analyzer automatically categorizes the topic of each conversation:
  - `tech_error`
  - `account_access`
  - `payment_issue`
  - `pricing_plan`
  - `refund_request`
  - `other`
- **Hidden dissatisfaction detection:** If a user says "thanks" but the core issue was not resolved, the interaction is flagged as `hidden_dissatisfaction`.
- **Agent mistake taxonomy:** Agents are audited for specific errors:
  - `wrong_customer_name`
  - `ignored_question`
  - `security_violation`
  - `incorrect_info`
  - `no_resolution`
  - `unnecessary_escalation`
  - `rude_tone`

---

## Technical Implementation

### 1. Determinism & Consistency

The analysis phase is strictly deterministic:

- **Greedy decoding:** `temperature = 0.0`
- **JSON enforcement:** Ensures machine-readable structured output
- **Stability:** Implements exponential backoff to handle `429 Resource Exhausted` errors during bulk processing

Determinism was validated in practice: the analyzer was run multiple times on the same randomly selected dialogues. Testing revealed only 1 discrepancy across 20 chats, corresponding to **~95% result stability** — a strong benchmark for an LLM-based system in a production environment.

---

### 2. Quality Scoring Rubric (1–5)

| Score | Rating | Criteria |
|-------|--------|----------|
| **5** | **Excellent** | Perfect execution: fast, polite, all questions answered, correct name usage. |
| **4** | **Good** | Issue resolved with good service; minor detail possibly missed. |
| **3** | **Average** | Issue partially resolved or robotic tone/missed questions. |
| **2** | **Poor** | Major mistakes: wrong info, ignored core question, wrong customer name. |
| **1** | **Fail** | Critical failure: rude tone, security violation (asked for password), or no help provided. |

---

## Installation & Usage

### 1. Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API Configuration

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_actual_api_key_here
```

Access to the large language models is provided via the Groq API.

### 3. Run Pipeline

```bash
# Step 1: Generate synthetic chats
python src/generate.py

# Step 2: Perform deterministic audit
python src/analyze.py
```
