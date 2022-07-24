from rest_framework.viewsets import ReadOnlyModelViewSet

from common.models import Region
from common.serializers import RegionSerializer


class RegionsViewSet(ReadOnlyModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
