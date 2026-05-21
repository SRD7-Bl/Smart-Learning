"""Data processing module for Smart Learning."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from Backend.Data_Access import DataAccessModule
from Frontend.qt_compat import QObject, pyqtSignal


class DataProcessingModule(QObject):
    """Organize parsed academic data, save it locally, and reload the saved result."""

    processing_succeeded = pyqtSignal(dict)
    processing_failed = pyqtSignal(str)
    processing_status = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        data_access_module: DataAccessModule | None = None,
    ) -> None:
        super().__init__(parent)
        self.data_access_module = data_access_module or DataAccessModule(self)
        self.data_access_module.academic_info_loaded.connect(self.processing_succeeded.emit)
        self.data_access_module.academic_info_saved.connect(self._reload_saved_academic_info)
        self.data_access_module.data_access_failed.connect(self.processing_failed.emit)

    def run_placeholder_pipeline(self) -> None:
        self.data_access_module.request_academic_info()

    def process_academic_info(self, parsed_academic_info: dict[str, Any]) -> None:
        try:
            processed = self._build_frontend_academic_info(parsed_academic_info)
        except (TypeError, ValueError) as error:
            self.processing_failed.emit(f"Data processing failed: {error}")
            return

        course_count = len(processed.get("courses", []))
        self.processing_status.emit(f"Processed {course_count} course(s). Saving academic info.")
        self.data_access_module.save_academic_info(processed)

    def _reload_saved_academic_info(self) -> None:
        self.processing_status.emit("Academic info saved. Reloading latest local data.")
        self.data_access_module.request_academic_info()

    def _build_frontend_academic_info(self, parsed_academic_info: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(parsed_academic_info, dict):
            raise TypeError("parsed academic info must be a dictionary.")

        existing_info = self._load_existing_academic_info()
        has_courses = "courses" in parsed_academic_info
        has_schedule = "schedule_days" in parsed_academic_info
        courses = (
            self._process_courses(parsed_academic_info.get("courses", []))
            if has_courses
            else existing_info.get("courses", [])
        )
        schedule_days = (
            self._process_schedule_days(parsed_academic_info.get("schedule_days", []))
            if has_schedule
            else existing_info.get("schedule_days", existing_info.get("schedule", []))
        )
        now = datetime.now().astimezone().isoformat(timespec="seconds")

        return {
            "student_name": existing_info.get("student_name", "Unknown"),
            "student_id": existing_info.get("student_id", "Unknown"),
            "last_updated": now,
            "summary": {
                "courses": len(courses),
                "assignments": sum(len(course.get("assignments", [])) for course in courses),
                "graded_assignments": self._count_assignments_by_status(courses, "graded"),
                "not_graded_assignments": self._count_assignments_by_status(courses, "not_graded"),
            },
            "schedule_days": schedule_days,
            "courses": courses,
        }

    def _load_existing_academic_info(self) -> dict[str, Any]:
        try:
            return self.data_access_module.load_academic_info_snapshot()
        except ValueError:
            return {}

    def _process_courses(self, raw_courses: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_courses, list):
            raise TypeError("parsed courses must be a list.")

        courses = []
        for index, raw_course in enumerate(raw_courses, start=1):
            if not isinstance(raw_course, dict):
                continue

            course = {
                "name": self._clean_text(raw_course.get("name")) or f"Course {index}",
                "description": self._clean_text(raw_course.get("description")) or "No description available.",
                "teacher": self._clean_text(raw_course.get("teacher")) or "Unavailable",
                "assignments": self._process_assignments(raw_course.get("assignments", [])),
            }
            courses.append(course)

        return courses

    def _process_assignments(self, raw_assignments: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_assignments, list):
            return []

        assignments = []
        for raw_assignment in raw_assignments:
            if not isinstance(raw_assignment, dict):
                continue

            assignment = {
                "name": self._clean_text(raw_assignment.get("name")) or "Unnamed Assignment",
                "type": self._clean_text(raw_assignment.get("type")) or "Uncategorized",
                "criterion": self._clean_text(raw_assignment.get("criterion")),
                "grade": self._clean_text(raw_assignment.get("grade")) or "N/A",
                "score": raw_assignment.get("score"),
                "max_score": raw_assignment.get("max_score"),
                "grade_status": self._clean_text(raw_assignment.get("grade_status")) or "unknown",
                "comment": self._clean_text(raw_assignment.get("comment")),
                "excluded_from_cumulative_grade": bool(raw_assignment.get("excluded_from_cumulative_grade", False)),
            }
            assignments.append(assignment)

        return assignments

    def _process_schedule_days(self, raw_schedule_days: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_schedule_days, list):
            return []

        schedule_days = []
        for raw_day in raw_schedule_days:
            if not isinstance(raw_day, dict):
                continue

            day = {
                "date": self._clean_text(raw_day.get("date")) or "Date unavailable",
                "day_type": self._clean_text(raw_day.get("day_type")) or "Day type unavailable",
                "day_index": raw_day.get("day_index"),
                "classes": self._process_schedule_classes(raw_day.get("classes", [])),
            }
            schedule_days.append(day)

        return schedule_days

    def _process_schedule_classes(self, raw_classes: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_classes, list):
            return []

        classes = []
        for raw_class in raw_classes:
            if not isinstance(raw_class, dict):
                continue

            item = {
                "time": self._clean_text(raw_class.get("time")) or "Time unavailable",
                "course_name": self._clean_text(raw_class.get("course_name")) or "Activity unavailable",
                "block": self._clean_text(raw_class.get("block")) or "N/A",
                "teacher": self._clean_text(raw_class.get("teacher")) or "Unavailable",
                "detail": self._clean_text(raw_class.get("detail")) or "No details available",
                "fields": raw_class.get("fields", {}) if isinstance(raw_class.get("fields", {}), dict) else {},
            }
            classes.append(item)

        return classes

    def _count_assignments_by_status(self, courses: list[dict[str, Any]], status: str) -> int:
        return sum(
            1
            for course in courses
            for assignment in course.get("assignments", [])
            if assignment.get("grade_status") == status
        )

    def _clean_text(self, value: Any) -> str:
        return "" if value is None else str(value).strip()
