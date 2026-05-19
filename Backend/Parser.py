"""Parser module for cleaning raw acquired academic data."""

from __future__ import annotations

import json
import re
from typing import Any

from Frontend.qt_compat import QObject, pyqtSignal


class ParserModule(QObject):
    """Parse raw course dictionaries from Data Acquisition into rough academic data."""

    parsing_succeeded = pyqtSignal(dict)
    parsing_failed = pyqtSignal(str)
    parsing_status = pyqtSignal(str)

    _excluded_marker = "exclude from cumulative grade"
    _leading_criterion_pattern = re.compile(r"^\s*\[([A-Za-z])\]\s*")
    _grade_pattern = re.compile(r"^\s*(?P<score>-{1,2}|\d+(?:\.\d+)?)\s*(?:/\s*(?P<max>\d+(?:\.\d+)?))?\s*$")
    _criterion_from_type_pattern = re.compile(r"\((?:Crit)?([A-Za-z])\)", re.IGNORECASE)

    def parse_course_info(self, raw_courses: list[dict[str, Any]]) -> None:
        """Parse acquired course dictionaries and print the rough JS-like structure."""
        try:
            parsed = self.parse_courses(raw_courses)
        except (TypeError, ValueError) as error:
            self.parsing_failed.emit(f"Parser failed: {error}")
            return

        # print("ParserModule rough academic info:")
        # print(json.dumps(parsed, ensure_ascii=False, indent=2))
        self.parsing_status.emit(f"Parsed {len(parsed.get('courses', []))} course(s).")
        self.parsing_succeeded.emit(parsed)

    def parse_courses(self, raw_courses: list[dict[str, Any]]) -> dict[str, Any]:
        """Return cleaned course data without saving it."""
        if not isinstance(raw_courses, list):
            raise TypeError("raw course data must be a list.")

        courses = []
        for raw_course in raw_courses:
            if not isinstance(raw_course, dict):
                continue

            course = self._parse_course(raw_course)
            if course["name"] or course["assignments"]:
                courses.append(course)

        return {"courses": courses}

    def _parse_course(self, raw_course: dict[str, Any]) -> dict[str, Any]:
        assignments = []
        for raw_assignment in raw_course.get("assignments", []):
            if not isinstance(raw_assignment, dict):
                continue

            assignment = self._parse_assignment(raw_assignment)
            if self._has_assignment_content(assignment):
                assignments.append(assignment)

        return {
            "name": self._clean_text(raw_course.get("name", "")),
            "description": self._clean_text(raw_course.get("description", "")),
            "teacher": self._clean_text(raw_course.get("teacher", "")),
            "assignments": assignments,
        }

    def _parse_assignment(self, raw_assignment: dict[str, Any]) -> dict[str, Any]:
        raw_name = self._clean_text(raw_assignment.get("name", ""))
        name, excluded, leading_criterion = self._parse_assignment_name(raw_name)
        grade_raw = self._clean_text(raw_assignment.get("grade", ""))
        score, max_score, grade_status = self._parse_grade(grade_raw)
        assignment_type = self._clean_text(raw_assignment.get("type", ""))
        type_criterion = self._parse_criterion_from_type(assignment_type)

        return {
            "name": name,
            "type": assignment_type,
            "criterion": type_criterion or leading_criterion,
            "grade": grade_raw,
            "score": score,
            "max_score": max_score,
            "grade_status": grade_status,
            "comment": self._clean_text(raw_assignment.get("comment", "")),
            "excluded_from_cumulative_grade": excluded,
        }

    def _parse_assignment_name(self, raw_name: str) -> tuple[str, bool, str]:
        lines = [line.strip() for line in raw_name.splitlines() if line.strip()]
        excluded = False
        content_lines = []
        for line in lines:
            if line.lower() == self._excluded_marker:
                excluded = True
                continue
            content_lines.append(line)

        cleaned_name = " ".join(content_lines).strip()
        criterion = ""
        match = self._leading_criterion_pattern.match(cleaned_name)
        if match:
            criterion = match.group(1).upper()
            cleaned_name = self._leading_criterion_pattern.sub("", cleaned_name, count=1).strip()

        return cleaned_name, excluded, criterion

    def _parse_grade(self, grade_raw: str) -> tuple[float | None, float | None, str]:
        if not grade_raw:
            return None, None, "missing"

        match = self._grade_pattern.match(grade_raw)
        if not match:
            return None, None, "unknown"

        score_raw = match.group("score")
        max_raw = match.group("max")
        max_score = self._number_or_none(max_raw)
        if score_raw.startswith("-"):
            return None, max_score, "not_graded"

        return self._number_or_none(score_raw), max_score, "graded"

    def _parse_criterion_from_type(self, assignment_type: str) -> str:
        match = self._criterion_from_type_pattern.search(assignment_type)
        return match.group(1).upper() if match else ""

    def _has_assignment_content(self, assignment: dict[str, Any]) -> bool:
        return any(
            assignment.get(field)
            for field in ("name", "grade", "comment")
        )

    def _clean_text(self, value: Any) -> str:
        text = "" if value is None else str(value)
        return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()

    def _number_or_none(self, value: str | None) -> float | None:
        if value in (None, ""):
            return None

        number = float(value)
        return int(number) if number.is_integer() else number
