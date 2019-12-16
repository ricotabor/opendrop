from typing import Type

from opendrop.app.core.imageacquirer import ImageAcquirerProvider
from opendrop.app.core.imageacquirer.filesystem import FilesystemAcquirerProvider
from opendrop.app.core.imageacquirer.usbcamera import USBCameraAcquirerProvider
from opendrop.appfw import WidgetComponent


class UnknownImageAcquirerProvider(Exception):
    """Raised when an unknown ImageAcquirerProvider is given to EditorResolver."""


class EditorResolver:
    @staticmethod
    def resolve(acquirer_provider: ImageAcquirerProvider) -> Type[WidgetComponent]:
        if isinstance(acquirer_provider, FilesystemAcquirerProvider):
            from .filesystem.component import FilesystemEditorComponent
            return FilesystemEditorComponent

        if isinstance(acquirer_provider, USBCameraAcquirerProvider):
            from .usbcamera.component import USBCameraEditorComponent
            return USBCameraEditorComponent

        raise UnknownImageAcquirerProvider('No editor found for {!r}'.format(acquirer_provider))
