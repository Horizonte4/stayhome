class PropertyPurchaseError(Exception):
    """Base exception for property purchase flow."""


class PropertyNotPurchasableError(PropertyPurchaseError):
    """Raised when a property cannot be purchased."""


class PropertyAlreadyPurchasedError(PropertyPurchaseError):
    """Raised when the property already has a sale contract."""


class OwnerCannotBuyOwnPropertyError(PropertyPurchaseError):
    """Raised when the owner tries to buy their own property."""
