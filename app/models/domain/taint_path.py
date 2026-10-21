from pydantic import BaseModel, Field
from typing import List, Optional

from app.models.domain.code_snippet import CodeSnippet


class TaintPath(BaseModel):
    rule_id: str 
    finding_id: str 
    source: CodeSnippet
    sink: CodeSnippet
    intermediate_nodes: List[CodeSnippet] = Field(default_factory=list)
    full_message: str = ""
    primary_file: str = ""
    severity: Optional[str] = None
    security_severity: Optional[float] = None 
    cwe_tags: List[str] = Field(default_factory=list)

    @property
    def all_nodes(self) -> List[CodeSnippet]:
        if self.source is self.sink:
            return [self.source]
        return [self.source, *self.intermediate_nodes, self.sink]
    
    @property
    def path_length(self) -> int:
        return len(self.all_nodes)