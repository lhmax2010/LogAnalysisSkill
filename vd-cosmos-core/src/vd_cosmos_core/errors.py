"""Stable errors: never expose subprocess output or backend exception text."""


class FlowError(Exception):
    def __init__(self, code, reason, **details):
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.details = details

    def as_dict(self):
        return {"ok": False, "exit_code": self.code, "error": self.reason,
                "details": self.details}


def unsupported(action):
    raise FlowError(6, "不支持", action=action)
