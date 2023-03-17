from baseObject import AutoPropertyObject
from .. import protocol
import weakref
from typing import Any, Dict, Iterable, List, TYPE_CHECKING
from autoSettingsUtils import driverSetting
from logHandler import log

if TYPE_CHECKING:
	from . import RemoteDriver


class SettingsAccessorBase(AutoPropertyObject):
	_driverRef: "weakref.ref[RemoteDriver]"
	driver: "RemoteDriver"
	_settingNames: List[str]
	cachePropertiesByDefault = True

	@classmethod
	def createFromSettings(cls, driver: "RemoteDriver", settings: Iterable[driverSetting.DriverSetting]):
		dct: Dict[str, Any] = {
			"__module__": __name__,
		}
		settingNames = []
		for s in settings:
			settingNames.append(s.id)
			dct[f"_get_{s.id}"] = cls._makeGetSetting(s.id)
			dct[f"_set_{s.id}"] = cls._makeSetSetting(s.id)
			if not isinstance(s, (driverSetting.BooleanDriverSetting, driverSetting.NumericDriverSetting)):
				dct[f"_get_{cls._getAvailableSettingsPropertyName(s.id)}"] = cls._makeGetAvailableSettings(s.id)
		return type("SettingsAccessor", (SettingsAccessorBase, ), dct)(driver, settingNames)

	def _get_driver(self):
		return self._driverRef()

	def __init__(self, driver: "RemoteDriver", settingNames: List[str]):
		self._driverRef = weakref.ref(driver)
		self._settingNames = settingNames
		for name in self._settingNames:
			self.driver.requestRemoteAttribute(self._getSettingAttributeName(name))

	@classmethod
	def _getSettingAttributeName(cls, setting: str) -> protocol.AttributeT:
		return protocol.SETTING_ATTRIBUTE_PREFIX + setting.encode("ASCII")

	@classmethod
	def _getAvailableSettingsPropertyName(cls, setting: str) -> str:
		return f"available{setting.capitalize()}s"

	@classmethod
	def _getAvailableSettingsAttributeName(cls, setting: str) -> protocol.AttributeT:
		return cls._getAvailableSettingsPropertyName(setting).encode("ASCII")

	@classmethod
	def _makeGetSetting(cls, setting: str):
		def _getSetting(self: SettingsAccessorBase):
			log.debug(f"Getting value for setting {setting}")
			attribute = self._getSettingAttributeName(setting)
			value = self.driver._attributeValueProcessor.getValue(attribute, fallBackToDefault=True)
			self.driver._queueFunctionOnMainThread(self.driver.requestRemoteAttribute, attribute)
			return value
		return _getSetting

	@classmethod
	def _makeSetSetting(cls, setting: str):
		def _setSetting(self: SettingsAccessorBase, value: Any):
			log.debug(f"Setting value for setting {setting} to {value}")
			attribute = self._getSettingAttributeName(setting)
			self.driver.setRemoteAttribute(attribute, self.driver._pickle(value))
			if self.driver._attributeValueProcessor.isAttributeSupported(attribute):
				self.driver._attributeValueProcessor.setValue(attribute, value)
		return _setSetting

	@classmethod
	def _makeGetAvailableSettings(cls, setting: str):
		def _getAvailableSettings(self: SettingsAccessorBase):
			attribute = self._getAvailableSettingsAttributeName(setting)
			try:
				return self.driver._attributeValueProcessor.getValue(attribute, fallBackToDefault=False)
			except KeyError:
				return self.driver.getRemoteAttribute(attribute)
		return _getAvailableSettings

	def __del__(self):
		if not self.driver:
			return
		try:
			for s in self._settingNames:
				self.driver._attributeValueProcessor.clearValue(self._getSettingAttributeName(s))
				self.driver._attributeValueProcessor.clearValue(self._getAvailableSettingsAttributeName(s))
		except Exception:
			log.debugWarning(f"Error deleting {self.__class__.__name__}", exc_info=True)
