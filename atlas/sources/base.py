"""SourceAdapter boundary for Research Atlas V3."""
from abc import ABC,abstractmethod

class SourceAdapterError(ValueError):
    pass

class SourceAdapter(ABC):
    adapter_id="abstract"
    @abstractmethod
    def resolve_company(self,query): ...
    @abstractmethod
    def discover_documents(self,company): ...
    @abstractmethod
    def company_facts(self,company): ...
    @abstractmethod
    def starter_pack(self,query): ...
