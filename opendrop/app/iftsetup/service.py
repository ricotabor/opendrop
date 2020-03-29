from injector import Module, Binder, inject, singleton

from opendrop.app.commonsetup.core.imageacquirer import ImageAcquirerSetupModule, ImageAcquirerSetupService
from opendrop.app.ift.component import IFTComponent
from opendrop.appfw import ActivityControllerService


class IFTSetupModule(Module):
    def configure(self, binder: Binder):
        binder.install(ImageAcquirerSetupModule)
        binder.bind(interface=IFTSetupService, to=IFTSetupService, scope=singleton)


class IFTSetupService:
    @inject
    def __init__(self, image_acquirer_setup: ImageAcquirerSetupService, activity_controller: ActivityControllerService) -> None:
        self._activity_controller = activity_controller
        self._image_acquirer_setup = image_acquirer_setup

    def set_up(self) -> None:
        try:
            image_acquirer = self._image_acquirer_setup.provide_acquirer()
        except Exception:
            raise

        self._activity_controller.start_activity(IFTComponent, image_acquirer=image_acquirer)