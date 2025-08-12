from typing import Any

class CSSParser:
    def parseString(self, css_text: str) -> Any: ...

class _SerializerPrefs:
    def useMinified(self) -> None: ...

class _Serializer:
    prefs: _SerializerPrefs

ser: _Serializer
