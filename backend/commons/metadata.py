from rest_framework.metadata import SimpleMetadata


class Metadata(SimpleMetadata):
    def determine_actions(self, request, view):
        return {}
