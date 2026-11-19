from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

TEST_LANGUAGE = "de"


class GermanTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.test_language = override_settings(LANGUAGE_CODE=TEST_LANGUAGE)
        self.test_language.enable()

    def teardown_test_environment(self, **kwargs):
        self.test_language.disable()
        super().teardown_test_environment(**kwargs)
