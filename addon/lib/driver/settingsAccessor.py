from baseObject import AutoPropertyObject
from .. import protocol
import weakref
from typing import Any, Iterable
from autoSettingsUtils import driverSetting


class SettingsAccessorBase(AutoPropertyObject):
	_driverRef: "weakref.ref[RemoteDriver]"
	driver: "RemoteDriver"

	@classmethod
	def createFromSettings(cls, driver: "RemoteDriver", settings: Iterable[driverSetting.DriverSetting]):
		dct = {"__module__": __name__}
		for setting in settings:
			dct[f"_get_{setting.id}"] = lambda self: self._getSetting(setting)
			dct[f"_set_{setting.id}"] = lambda self, value: self._setSetting(setting, value)
			if not isinstance(setting, (driverSetting.BooleanDriverSetting, driverSetting.NumericDriverSetting)):
				dct[cls._getAvailableSettingsPropertyName(setting.id)] = lambda self: self.__getAvailableSettings(setting)
		return type("SettingsAccessor", (SettingsAccessorBase, ), dct)(driver)

	def _get_driver(self):
		return self._driverRef()

	def __init__(self, driver: "RemoteDriver"):
		self._driverRef = weakref.ref(driver)

	@classmethod
	def _getSettingAttributeName(cls, setting: str) -> protocol.AttributeT:
		return protocol.SETTING_ATTRIBUTE_PREFIX + setting.encode("ASCII")

	@classmethod
	def _getAvailableSettingsPropertyName(cls, setting: str) -> str:
		return f"available{setting.capitalize()}s"

	@classmethod
	def _getAvailableSettingsAttributeName(cls, setting: str) -> protocol.AttributeT:
		return cls._getAvailableSettingsPropertyName(setting).encode("ASCII")

	def _getSetting(self, name: str):
		return self.driver.getRemoteAttribute(self._getSettingAttributeName(name))

	def _setSetting(self, name: str, value: Any):
		attribute = self._getSettingAttributeName(name)
		self.driver.setRemoteAttribute(attribute, self.driver._pickle(name))
		if self.driver._attributeValueProcessor.isAttributeSupported(attribute):
			self.driver._attributeValueProcessor.SetValue(attribute, value)

	def _getAvailableSettings(self, setting: str):
		attribute = self._getAvailableSettingsAttributeName(setting)
		try:
			return self.driver._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
		except KeyError:
			return self.driver.getRemoteAttribute(attribute)
