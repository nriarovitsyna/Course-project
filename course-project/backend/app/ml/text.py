import re
from typing import Optional

from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    Doc,
)

from app.schemas.ml import TextAnalysisRequest, TextAnalysisResponse
from app.ml.utils import tokenize, safe_lower

# Инициализация Natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
ner_tagger = NewsNERTagger(emb)


# Справочники: Города миллионики
MILLION_CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
    "Казань", "Нижний Новгород", "Челябинск", "Самара", "Омск",
    "Ростов-на-Дону", "Уфа", "Красноярск", "Пермь", "Воронеж", "Волгоград",
]


CITY_ALIASES = {
    "москва": "Москва",
    "мск": "Москва",
    "спб": "Санкт-Петербург",
    "питер": "Санкт-Петербург",
    "санкт-петербург": "Санкт-Петербург",
    "нск": "Новосибирск",
    "екб": "Екатеринбург",
    "ростов": "Ростов-на-Дону",
    "нижний": "Нижний Новгород",
    "нижний новгород": "Нижний Новгород",
}

LEVEL_MAP = {
    "бакалавриат": "Бакалавриат",
    "бакалавр": "Бакалавриат",
    "магистратура": "Магистратура",
    "магистр": "Магистратура",
    "специалитет": "Специалитет",
    "специалист": "Специалитет",
    "аспирантура": "Аспирантура",
    "аспирант": "Аспирантура",
}

FORMAT_MAP = {
    "очная": "Очная",
    "очно": "Очная",
    "очный": "Очная",
    "заочная": "Заочная",
    "заочно": "Заочная",
    "заочный": "Заочная",
    "очно-заочная": "Очно-заочная",
    "очно заочная": "Очно-заочная",
    "дистанционная": "Дистанционная",
    "дистанционно": "Дистанционная",
    "онлайн": "Дистанционная",
    "вечерняя": "Вечерняя",
    "вечернее": "Вечерняя",
}

LANGUAGE_MAP = {
    "русский": "Русский",
    "на русском": "Русский",
    "английский": "English",
    "на английском": "English",
    "english": "English",
}

ACCREDITATION_MAP = {
    "государственный": "государственный",
    "гос": "государственный",
    "частный": "частный",
}

# IT-only словарь факультетов и направлений
FACULTY_MAP = {
    # Аббревиатуры факультетов / школ
    "фкн": "Факультет компьютерных наук",
    "фпми": "Физтех-школа прикладной математики и информатики",
    "фпиикт": "Факультет программной инженерии и компьютерной техники",
    "мфктиу": "Мегафакультет компьютерных технологий и управления",
    "суир": "Факультет систем управления и робототехники",

    # Базовые IT-направления
    "пми": "Прикладная математика и информатика",
    "прикладная математика": "Прикладная математика и информатика",
    "прикладная математика и информатика": "Прикладная математика и информатика",
    "информатика": "Информатика",
    "компьютерные науки": "Компьютерные науки",
    "computer science": "Компьютерные науки",
    "программная инженерия": "Программная инженерия",
    "программирование": "Программная инженерия",
    "прога": "Программная инженерия",
    "информационные системы": "Информационные системы и технологии",
    "информационные системы и технологии": "Информационные системы и технологии",
    "ист": "Информационные системы и технологии",

    # AI / ML / DS
    "data science": "Data Science",
    "датасаенс": "Data Science",
    "анализ данных": "Data Science",
    "машинное обучение": "Machine Learning",
    "ml": "Machine Learning",
    "искусственный интеллект": "Artificial Intelligence",
    "ии": "Artificial Intelligence",
    "ai": "Artificial Intelligence",
    "big data": "Big Data",
    "большие данные": "Big Data",

    # Системные и прикладные направления
    "кибербезопасность": "Информационная безопасность",
    "информационная безопасность": "Информационная безопасность",
    "системное программирование": "Системное программирование",
    "робототехника": "Робототехника",
}

UNIVERSITY_ALIASES = {
    "мгу": "Московский государственный университет имени М.В. Ломоносова",
    "вшэ": "Национальный исследовательский университет Высшая школа экономики",
    "ниу вшэ": "Национальный исследовательский университет Высшая школа экономики",
    "мфти": "Московский физико-технический институт",
    "фпми мфти": "Московский физико-технический институт",
    "маи": "Московский авиационный институт",
    "бауманка": "Московский государственный технический университет им. Н.Э. Баумана",
    "мгту": "Московский государственный технический университет им. Н.Э. Баумана",
    "итмо": "Университет ИТМО",
    "спбгу": "Санкт-Петербургский государственный университет",
    "мифи": "Национальный исследовательский ядерный университет МИФИ",
    "мисис": "Национальный исследовательский технологический университет МИСИС",
    "иннополис": "Университет Иннополис",
}

DURATION_TEXT_MAP = {
    "2 года": 2.0,
    "два года": 2.0,
    "4 года": 4.0,
    "четыре года": 4.0,
    "5 лет": 5.0,
    "пять лет": 5.0,
    "6 лет": 6.0,
    "шесть лет": 6.0,
}


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def unique_keep_order(items: list[str]) -> list[str]:
    """Удаляет дубликаты, сохраняя порядок элементов."""
    return list(dict.fromkeys([x for x in items if x and str(x).strip()]))


def normalize_spaces_and_numbers(text: str) -> str:
    """Нормализует пробелы и склеивает числа вида 300 000 -> 300000."""
    normalized = text.lower().replace("\xa0", " ")
    normalized = re.sub(r"(\d)\s+(\d{3})(?!\d)", r"\1\2", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _to_float(value: str) -> Optional[float]:
    """Преобразует строку в число float, если это возможно."""
    try:
        return float(value.replace(",", "."))
    except Exception:
        return None


def _to_rubles(num_str: str, unit: str) -> Optional[float]:
    """Переводит число с единицей измерения в рубли."""
    value = _to_float(num_str)
    if value is None:
        return None

    unit = safe_lower(unit)
    if re.search(r"млн|миллион", unit):
        return value * 1_000_000
    if re.search(r"тыс|тысяч|тысячи|к|k", unit):
        return value * 1_000
    return value


def normalize_city_name(city: str) -> str:
    """Приводит название города к каноничному виду."""
    city_lower = safe_lower(city)
    if city_lower in CITY_ALIASES:
        return CITY_ALIASES[city_lower]
    return city.strip().title()


def build_doc(text: str) -> Doc:
    """Создаёт Natasha Doc и размечает сущности."""
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)
    doc.tag_ner(ner_tagger)
    return doc


# ---------------------------------------------------------------------------
# Извлечение сущностей Natasha
# ---------------------------------------------------------------------------

def extract_names(text: str) -> list[str]:
    """Извлекает имена людей из текста через Natasha."""
    doc = build_doc(text)
    names = []

    for span in doc.spans:
        if span.type == "PER":
            span.normalize(morph_vocab)
            value = span.normal.strip()
            if value:
                names.append(value)

    return unique_keep_order(names)


def _extract_orgs_natasha(text: str) -> list[str]:
    """Извлекает названия организаций из текста через Natasha."""
    doc = build_doc(text)
    orgs = []

    for span in doc.spans:
        if span.type == "ORG":
            span.normalize(morph_vocab)
            value = span.normal.strip()
            if value:
                orgs.append(value)

    return unique_keep_order(orgs)


def _extract_cities_natasha(text: str) -> list[str]:
    """Извлекает города через Natasha."""
    doc = build_doc(text)
    cities = []

    for span in doc.spans:
        if span.type == "LOC":
            span.normalize(morph_vocab)
            city = span.normal.strip()
            if city:
                cities.append(normalize_city_name(city))

    return unique_keep_order(cities)


# ---------------------------------------------------------------------------
# Категориальные поля
# ---------------------------------------------------------------------------

def extract_cities(text: str) -> list[str]:
    """Извлекает города, включая алиасы и запросы про миллионники."""
    text_lower = safe_lower(text)
    cities = _extract_cities_natasha(text)

    for alias, canonical in CITY_ALIASES.items():
        if alias in text_lower and canonical not in cities:
            cities.append(canonical)

    if re.search(r"миллионник|миллионники", text_lower):
        for city in MILLION_CITIES:
            if city not in cities:
                cities.append(city)

    return unique_keep_order(cities)


def extract_universities(text: str) -> list[str]:
    """Извлекает университеты через Natasha ORG и словарь алиасов."""
    text_lower = safe_lower(text)
    universities = _extract_orgs_natasha(text)

    for alias, canonical in UNIVERSITY_ALIASES.items():
        if alias in text_lower and canonical not in universities:
            universities.append(canonical)

    return unique_keep_order(universities)


def extract_faculties(text: str) -> list[str]:
    """Извлекает IT-направления и факультеты по ключевым словам и аббревиатурам."""
    text_lower = safe_lower(text)
    faculties = []

    for keyword, faculty in FACULTY_MAP.items():
        if len(keyword) <= 4:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, text_lower) and faculty not in faculties:
                faculties.append(faculty)
        else:
            if keyword in text_lower and faculty not in faculties:
                faculties.append(faculty)

    return unique_keep_order(faculties)


def extract_levels(text: str) -> list[str]:
    """Извлекает уровни образования."""
    text_lower = safe_lower(text)
    levels = []

    for keyword, level in LEVEL_MAP.items():
        if keyword in text_lower and level not in levels:
            levels.append(level)

    return unique_keep_order(levels)


def extract_study_formats(text: str) -> list[str]:
    """Извлекает форматы обучения."""
    text_lower = safe_lower(text)
    formats = []

    for keyword, fmt in FORMAT_MAP.items():
        if keyword in text_lower and fmt not in formats:
            formats.append(fmt)

    return unique_keep_order(formats)


def extract_languages(text: str) -> list[str]:
    """Извлекает языки обучения."""
    text_lower = safe_lower(text)
    languages = []

    for keyword, lang in LANGUAGE_MAP.items():
        if keyword in text_lower and lang not in languages:
            languages.append(lang)

    return unique_keep_order(languages)


def extract_accreditations(text: str) -> list[str]:
    """Извлекает типы аккредитации."""
    text_lower = safe_lower(text)
    accreditations = []

    for keyword, value in ACCREDITATION_MAP.items():
        if keyword in text_lower and value not in accreditations:
            accreditations.append(value)

    return unique_keep_order(accreditations)


def extract_budget(text: str) -> Optional[bool]:
    """Определяет, ищет ли пользователь бюджет или платное обучение."""
    text_lower = safe_lower(text)

    if re.search(r"бюджет(?:ное|ные|ных|ная|ные места|ных мест)?", text_lower):
        return True

    if re.search(r"платн(?:ое|ые|ая|о|ой основе)", text_lower):
        return False

    return None


# ---------------------------------------------------------------------------
# Числовые поля
# ---------------------------------------------------------------------------

def extract_price_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """Извлекает минимальную и максимальную стоимость обучения в рублях только при наличии ценового контекста."""
    normalized = normalize_spaces_and_numbers(text)

    unit_pattern = r"(тыс(?:яч[аи])?\.?|млн|миллион(?:а|ов)?|руб(?:лей|ля)?|р\b|к|k)?"
    price_context = r"(?:стоимость|цена|обучение|обучения|плата|платное|платного|руб|рублей|р\b|тыс|млн)"

    price_min = None
    price_max = None

    max_patterns = [
        rf"{price_context}\D{{0,20}}(?:до|не\s+более|не\s+дороже|не\s+больше|максимум|макс\.?)\s+([\d.,]+)\s*{unit_pattern}",
        rf"(?:до|не\s+более|не\s+дороже|не\s+больше|максимум|макс\.?)\s+([\d.,]+)\s*{unit_pattern}\D{{0,20}}{price_context}",
        rf"{price_context}\D{{0,20}}дешевле\s+([\d.,]+)\s*{unit_pattern}",
    ]

    min_patterns = [
        rf"{price_context}\D{{0,20}}(?:от|не\s+менее|не\s+меньше|минимум|мин\.?)\s+([\d.,]+)\s*{unit_pattern}",
        rf"(?:от|не\s+менее|не\s+меньше|минимум|мин\.?)\s+([\d.,]+)\s*{unit_pattern}\D{{0,20}}{price_context}",
    ]

    exact_patterns = [
        rf"{price_context}\D{{0,20}}([\d.,]+)\s*{unit_pattern}",
    ]

    for pattern in max_patterns:
        m = re.search(pattern, normalized)
        if m:
            price_max = _to_rubles(m.group(1), m.group(2) or "")
            break

    for pattern in min_patterns:
        m = re.search(pattern, normalized)
        if m:
            price_min = _to_rubles(m.group(1), m.group(2) or "")
            break

    if price_min is None and price_max is None:
        for pattern in exact_patterns:
            m = re.search(pattern, normalized)
            if m:
                value = _to_rubles(m.group(1), m.group(2) or "")
                if value is not None and value >= 1000:
                    price_max = value
                    break

    return price_min, price_max


def extract_duration_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """Извлекает диапазон длительности обучения в годах."""
    text_lower = safe_lower(text)
    values = []

    for phrase, years in DURATION_TEXT_MAP.items():
        if phrase in text_lower:
            values.append(years)

    match_range = re.search(
        r"от\s+(\d+(?:[.,]\d+)?)\s*(?:год|года|лет)\s+до\s+(\d+(?:[.,]\d+)?)\s*(?:год|года|лет)",
        text_lower,
    )
    if match_range:
        left = _to_float(match_range.group(1))
        right = _to_float(match_range.group(2))
        if left is not None and right is not None:
            values.extend([left, right])

    match_max = re.search(r"(?:до|не\s+более)\s+(\d+(?:[.,]\d+)?)\s*(?:год|года|лет)", text_lower)
    match_min = re.search(r"(?:от|не\s+менее)\s+(\d+(?:[.,]\d+)?)\s*(?:год|года|лет)", text_lower)

    min_val = _to_float(match_min.group(1)) if match_min else None
    max_val = _to_float(match_max.group(1)) if match_max else None

    if values:
        base_min = min(values)
        base_max = max(values)
        min_val = base_min if min_val is None else min(min_val, base_min)
        max_val = base_max if max_val is None else max(max_val, base_max)

    return min_val, max_val


def extract_budget_score_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """Извлекает диапазон проходных баллов на бюджет."""
    text_lower = normalize_spaces_and_numbers(text)

    score_min = None
    score_max = None

    patterns_min = [
        r"(?:проходн\w*\s+балл\w*\s+на\s+бюджет|на\s+бюджет\s+проходн\w*|бюджет\w*\s+балл\w*)\s+от\s+(\d{2,3})",
        r"(?:проходн\w*\s+балл\w*|проходн\w*|балл\w*)\s+от\s+(\d{2,3})",
    ]

    patterns_max = [
        r"(?:проходн\w*\s+балл\w*\s+на\s+бюджет|на\s+бюджет\s+проходн\w*|бюджет\w*\s+балл\w*)\s+(?:до|не\s+более)\s+(\d{2,3})",
        r"(?:проходн\w*\s+балл\w*|проходн\w*|балл\w*)\s+(?:до|не\s+более)\s+(\d{2,3})",
    ]

    for pattern in patterns_min:
        m = re.search(pattern, text_lower)
        if m:
            value = _to_float(m.group(1))
            if value is not None and 50 <= value <= 400:
                score_min = value
                break

    for pattern in patterns_max:
        m = re.search(pattern, text_lower)
        if m:
            value = _to_float(m.group(1))
            if value is not None and 50 <= value <= 400:
                score_max = value
                break

    if score_min is None and score_max is None:
        m = re.search(r"(?:проходн\w*\s+балл\w*|проходн\w*|балл\w*)\D{0,10}(\d{2,3})", text_lower)
        if m:
            value = _to_float(m.group(1))
            if value is not None and 50 <= value <= 400:
                score_min = value

    return score_min, score_max


def extract_paid_score_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """Извлекает диапазон минимальных баллов на платные места."""
    text_lower = normalize_spaces_and_numbers(text)

    score_min = None
    score_max = None

    patterns_min = [
        r"(?:на\s+платн\w*|платн\w*\s+мест\w*)\D{0,15}(?:от|не\s+менее)\s+(\d{2,3})",
        r"(?:платн\w*\s+балл\w*|минимальн\w*\s+балл\w*\s+на\s+платн\w*)\s+от\s+(\d{2,3})",
    ]

    patterns_max = [
        r"(?:на\s+платн\w*|платн\w*\s+мест\w*)\D{0,15}(?:до|не\s+более)\s+(\d{2,3})",
        r"(?:платн\w*\s+балл\w*|минимальн\w*\s+балл\w*\s+на\s+платн\w*)\s+(?:до|не\s+более)\s+(\d{2,3})",
    ]

    for pattern in patterns_min:
        m = re.search(pattern, text_lower)
        if m:
            value = _to_float(m.group(1))
            if value is not None and 0 <= value <= 400:
                score_min = value
                break

    for pattern in patterns_max:
        m = re.search(pattern, text_lower)
        if m:
            value = _to_float(m.group(1))
            if value is not None and 0 <= value <= 400:
                score_max = value
                break

    return score_min, score_max


def extract_budget_places_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """Извлекает диапазон количества бюджетных мест."""
    text_lower = normalize_spaces_and_numbers(text)
    places_min = None
    places_max = None

    budget_context = r"(?:бюджетн\w*\s+мест\w*|мест\w*\s+на\s+бюджет\w*|количеств\w*\s+бюджет\w*\s+мест\w*)"

    min_patterns = [
        rf"{budget_context}\D{{0,20}}(?:от|не\s+менее|не\s+меньше|минимум|более|больше|свыше|как\s+минимум)\s+(\d+)",
        rf"(?:от|не\s+менее|не\s+меньше|минимум|более|больше|свыше|как\s+минимум)\s+(\d+)\D{{0,20}}{budget_context}",
    ]

    max_patterns = [
        rf"{budget_context}\D{{0,20}}(?:до|не\s+более|не\s+больше|максимум|менее|меньше)\s+(\d+)",
        rf"(?:до|не\s+более|не\s+больше|максимум|менее|меньше)\s+(\d+)\D{{0,20}}{budget_context}",
    ]

    for pattern in min_patterns:
        m = re.search(pattern, text_lower)
        if m:
            places_min = _to_float(m.group(1))
            break

    for pattern in max_patterns:
        m = re.search(pattern, text_lower)
        if m:
            places_max = _to_float(m.group(1))
            break

    return places_min, places_max


def extract_paid_places_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """Извлекает диапазон количества платных мест."""
    text_lower = normalize_spaces_and_numbers(text)
    places_min = None
    places_max = None

    paid_context = r"(?:платн\w*\s+мест\w*|мест\w*\s+на\s+платн\w*|количеств\w*\s+платн\w*\s+мест\w*)"

    min_patterns = [
        rf"{paid_context}\D{{0,20}}(?:от|не\s+менее|не\s+меньше|минимум|более|больше|свыше|как\s+минимум)\s+(\d+)",
        rf"(?:от|не\s+менее|не\s+меньше|минимум|более|больше|свыше|как\s+минимум)\s+(\d+)\D{{0,20}}{paid_context}",
    ]

    max_patterns = [
        rf"{paid_context}\D{{0,20}}(?:до|не\s+более|не\s+больше|максимум|менее|меньше)\s+(\d+)",
        rf"(?:до|не\s+более|не\s+больше|максимум|менее|меньше)\s+(\d+)\D{{0,20}}{paid_context}",
    ]

    for pattern in min_patterns:
        m = re.search(pattern, text_lower)
        if m:
            places_min = _to_float(m.group(1))
            break

    for pattern in max_patterns:
        m = re.search(pattern, text_lower)
        if m:
            places_max = _to_float(m.group(1))
            break

    return places_min, places_max


# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------

def analyze_text(req: TextAnalysisRequest) -> TextAnalysisResponse:
    """Разбирает пользовательский текст и превращает его в набор фильтров."""
    text = req.text

    detected_names = extract_names(text)
    detected_cities = extract_cities(text)
    detected_faculties = extract_faculties(text)
    detected_universities = extract_universities(text)
    detected_levels = extract_levels(text)
    detected_budget = extract_budget(text)
    detected_languages = extract_languages(text)
    detected_accreditations = extract_accreditations(text)
    detected_study_formats = extract_study_formats(text)

    detected_duration_min, detected_duration_max = extract_duration_range(text)
    detected_price_min, detected_price_max = extract_price_range(text)

    detected_budget_score_min, detected_budget_score_max = extract_budget_score_range(text)
    detected_paid_score_min, detected_paid_score_max = extract_paid_score_range(text)

    detected_budget_places_min, detected_budget_places_max = extract_budget_places_range(text)
    detected_paid_places_min, detected_paid_places_max = extract_paid_places_range(text)

    tokens = tokenize(safe_lower(text))
    keywords = unique_keep_order(tokens)[:30]

    return TextAnalysisResponse(
        keywords=keywords,
        detected_names=detected_names,
        detected_cities=detected_cities,
        detected_faculties=detected_faculties,
        detected_universities=detected_universities,
        detected_levels=detected_levels,
        detected_budget=detected_budget,
        detected_languages=detected_languages,
        detected_duration_min=detected_duration_min,
        detected_duration_max=detected_duration_max,
        detected_accreditations=detected_accreditations,
        detected_study_formats=detected_study_formats,
        detected_price_min=detected_price_min,
        detected_price_max=detected_price_max,
        detected_budget_score_min=detected_budget_score_min,
        detected_budget_score_max=detected_budget_score_max,
        detected_paid_score_min=detected_paid_score_min,
        detected_paid_score_max=detected_paid_score_max,
        detected_budget_places_min=detected_budget_places_min,
        detected_budget_places_max=detected_budget_places_max,
        detected_paid_places_min=detected_paid_places_min,
        detected_paid_places_max=detected_paid_places_max,
        normalized_query=" ".join(tokens),
    )