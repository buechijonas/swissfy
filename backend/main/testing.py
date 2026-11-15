from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

SOURCE_LANGUAGE = "de"


class SourceLanguageTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.source_language = override_settings(LANGUAGE_CODE=SOURCE_LANGUAGE)
        self.source_language.enable()

    def teardown_test_environment(self, **kwargs):
        self.source_language.disable()
        super().teardown_test_environment(**kwargs)
