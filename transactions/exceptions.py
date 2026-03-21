class PropertyPurchaseError(Exception):
    """Base exception for property purchase flow."""


class PropertyNotPurchasableError(PropertyPurchaseError):
    """Raised when a property cannot be purchased."""


class PropertyAlreadyPurchasedError(PropertyPurchaseError):
    """Raised when the property already has a sale contract."""


class OwnerCannotBuyOwnPropertyError(PropertyPurchaseError):
    """Raised when the owner tries to buy their own property."""


class PurchaseRequestError(Exception):
    """Base exception for purchase request flow."""


class DuplicatePurchaseRequestError(PurchaseRequestError):
    """Raised when the buyer already has a request for the property."""


class PurchaseRequestPermissionError(PurchaseRequestError):
    """Raised when the user has no permission to change the request."""
