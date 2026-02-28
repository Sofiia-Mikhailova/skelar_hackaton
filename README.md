# 🇺🇦 AI Support Quality Analysis Pipeline / 🇬🇧 AI Support Quality Analysis Pipeline

## 🇺🇦 Огляд проєкту

Цей репозиторій містить професійну pipeline-систему для генерації синтетичних датасетів клієнтської підтримки з високою варіативністю та проведення високоточного аудиту якості за допомогою великих мовних моделей (LLM).

Система спеціально розроблена для вирішення проблеми **«Прихованого невдоволення»**: виявлення випадків, коли клієнт виглядає ввічливим (наприклад, каже «Дякую»), навіть якщо його проблема фактично залишилася невирішеною агентом.


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

### 1. Генерація з високою варіативністю (`generate.py`)

Щоб протестувати модель на реалістичних і «шумних» даних, генератор використовує `llama-3.1-8b-instant` із **temperature = 0.8** для досягнення максимальної різноманітності.

**Логіка людської поведінки:**

- **Природний ритм повідомлень:** клієнт надсилає привітання та проблему у **2–3 окремих повідомленнях** (наприклад, «hi» → «i have a problem»).
- **Мовна реалістичність:** використання сленгу, скорочень (thx, ok then, noted), відсутність великих літер.
- **Емоційний «шум»:** періодичне використання **ALL CAPS**, граматичних помилок або надмірної пунктуації.
- **Різні сценарії завершення:** не всі діалоги завершуються вирішенням. Генеруються сценарії «Customer Silent», де клієнт перестає відповідати, перевіряючи дотримання протоколів бездіяльності.

### 2. Аналіз за принципом «Спочатку результат» (`analyze.py`)

Аналізатор використовує `llama-3.3-70b-versatile` з **temperature = 0.0** та фіксованим seed для забезпечення детермінованості.

**Ключові аналітичні принципи:**

- **Результат важливіший за тон:** Тон клієнта ≠ задоволення. Агресивний клієнт, чию проблему вирішено, позначається як `satisfied`, тоді як ввічливий клієнт із невирішеним питанням — як `unsatisfied`.
- **Виявлення прихованого невдоволення:** Якщо користувач каже «thanks», але основний запит не виконано — система позначає взаємодію як невдалу.
- **Таксономія помилок агента:** Агент перевіряється на конкретні помилки:
  - `wrong_customer_name`
  - `ignored_question`
  - `security_violation`
  - `incorrect_info`
  - `no_resolution`


## Технічна реалізація

### 1. Детермінованість та узгодженість

Фаза аналізу суворо детермінована відповідно до вимог:

- **Greedy decoding:** `temperature = 0.0`
- **Примусовий JSON-режим:** гарантує структурований машинозчитуваний результат
- **Стабільність:** реалізовано exponential backoff для обробки помилок `429 Resource Exhausted` під час масової обробки


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

The system is specifically engineered to solve the **"Hidden Dissatisfaction"** challenge: identifying cases where a customer appears polite (e.g., saying "Thank you") while their underlying issue remains unresolved by the agent.


## Project Structure

The project follows a modular, production-ready architecture:

- **`src/`** – Core application logic
  - `generate.py` – Synthetic dialogue generation engine
  - `analyze.py` – Deterministic quality auditing engine
  - `llm_client.py` – Centralized Groq API client with structured JSON handling
- **`data/`** – Storage for clean datasets and analysis results
- **`utils/`** – Helper scripts for benchmarking, reference data, and determinism testing
- **`.env.example`** – Template for secure API key management


## Core Logic & Prompt Engineering

### 1. High-Variance Generation (`generate.py`)

To stress-test the model against realistic, noisy data, the generator uses `llama-3.1-8b-instant` with **temperature = 0.8** to maximize diversity.

**Human-Centric Diversity Logic:**

- **Natural message pacing:** The customer sends greetings and the actual problem across **2–3 separate messages** (e.g., "hi" → "i have a problem").
- **Linguistic realism:** Incorporates slang, short abbreviations (thx, ok then, noted), and missing capitalization.
- **Emotional noise:** Occasionally uses **ALL CAPS**, grammar mistakes, or excessive punctuation to simulate frustration.
- **Varied chat endings:** Not all chats end with resolution. "Customer Silent" scenarios simulate inactivity and test protocol adherence.


### 2. Resolution-First Analysis (`analyze.py`)

The analyzer uses `llama-3.3-70b-versatile` with **temperature = 0.0** and a fixed seed to ensure deterministic audits.

**Key Analytical Pillars:**

- **Outcome over sentiment:** Customer tone ≠ satisfaction. An aggressive customer whose issue is resolved is marked `satisfied`, while a polite customer with an unresolved issue is marked `unsatisfied`.
- **Hidden dissatisfaction detection:** If a user says "thanks" but the core issue was not resolved, the interaction is flagged as a failure.
- **Agent mistake taxonomy:** Agents are audited for specific errors:
  - `wrong_customer_name`
  - `ignored_question`
  - `security_violation`
  - `incorrect_info`
  - `no_resolution`


## Technical Implementation

### 1. Determinism & Consistency

The analysis phase is strictly deterministic:

- **Greedy decoding:** `temperature = 0.0`
- **JSON enforcement:** Ensures machine-readable structured output
- **Stability:** Implements exponential backoff to handle `429 Resource Exhausted` errors during bulk processing


### 2. Quality Scoring Rubric (1–5)

| Score | Rating | Criteria |
|-------|--------|----------|
| **5** | **Excellent** | Perfect execution: fast, polite, all questions answered, correct name usage. |
| **4** | **Good** | Issue resolved with good service; minor detail possibly missed. |
| **3** | **Average** | Issue partially resolved or robotic tone/missed questions. |
| **2** | **Poor** | Major mistakes: wrong info, ignored core question, wrong customer name. |
| **1** | **Fail** | Critical failure: rude tone, security violation (asked for password), or no help provided. |


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

### 3. Run Pipeline

```bash
# Step 1: Generate synthetic chats
python src/generate.py

# Step 2: Perform deterministic audit
python src/analyze.py
```
