from dataclasses import dataclass


class ServiceError(Exception):
    status_code = 500
    code = "service_error"
    message = "Internal service error"


class ModelNotReadyError(ServiceError):
    status_code = 503
    code = "model_not_ready"
    message = "Model is not ready"


class ModelLoadError(ServiceError):
    status_code = 503
    code = "model_load_failed"
    message = "Model artifacts could not be loaded"


@dataclass
class ErrorPayload:
    request_id: str
    code: str
    message: str
