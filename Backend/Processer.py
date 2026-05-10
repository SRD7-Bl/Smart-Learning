"""Data processing module placeholder for Smart Learning."""

from __future__ import annotations

from Backend.Data_Access import DataAccessModule
from Frontend.qt_compat import QObject, pyqtSignal


class DataProcessingModule(QObject):
    """Temporary processing pipeline endpoint for refresh requests."""

    processing_succeeded = pyqtSignal(dict)
    processing_failed = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        data_access_module: DataAccessModule | None = None,
    ) -> None:
        super().__init__(parent)
        self.data_access_module = data_access_module or DataAccessModule(self)
        self.data_access_module.academic_info_loaded.connect(self.processing_succeeded.emit)
        self.data_access_module.data_access_failed.connect(self.processing_failed.emit)

    def run_placeholder_pipeline(self) -> None:
        self.data_access_module.request_academic_info()
