from rest_framework.reverse import reverse
from rest_framework.serializers import (HyperlinkedIdentityField,
                                        ModelSerializer, SerializerMethodField)

from common.models import Region


class RegionSerializer(ModelSerializer):
    url = HyperlinkedIdentityField(view_name='common:region-detail')
    reservoirs = SerializerMethodField()

    class Meta:
        model = Region
        fields = '__all__'

    def get_reservoirs(self, obj):
        view_name = 'reservoirs:reservoir-list'
        base_url = reverse(view_name, request=self.context['request'])
        return f'{base_url}?region={obj.slug}'


class RegionNestedSerializer(ModelSerializer):
    class Meta:
        model = Region
        exclude = ('id', )
