from typing import List, Any
from app.schemas.ml import CompareRequest, CompareResponse, CompareRow
from app.ml.features import program_to_dict


def compare_programs(programs: List[Any]) -> CompareResponse:
    if not programs:
        return CompareResponse(rows=[])

    data = [program_to_dict(p) for p in programs]

    def as_map(field: str):
        return {
            str(item["id"]): item.get(field)
            for item in data
        }

    rows = [
        CompareRow(criterion="Название", values=as_map("name")),
        CompareRow(criterion="Университет", values=as_map("university_name")),
        CompareRow(criterion="Город", values=as_map("city")),
        CompareRow(criterion="Факультет", values=as_map("faculty")),
        CompareRow(criterion="Уровень", values=as_map("level")),
        CompareRow(criterion="Формат", values=as_map("study_format")),
        CompareRow(criterion="Цена", values=as_map("price")),
        CompareRow(criterion="Бюджет", values=as_map("has_budget")),
    ]

    return CompareResponse(rows=rows)