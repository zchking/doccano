from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from rest_framework.exceptions import ValidationError


from .models import Label, Project, Document
from .models import TextClassificationProject, SequenceLabelingProject, Seq2seqProject
from .models import DocumentAnnotation, SequenceAnnotation, Seq2seqAnnotation


class LabelSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        if 'prefix_key' not in attrs and 'suffix_key' not in attrs:
            return super().validate(attrs)

        # Don't allow shortcut key not to have a suffix key.
        if attrs['prefix_key'] and not attrs['suffix_key']:
            raise ValidationError('Shortcut key may not have a suffix key.')

        # Don't allow to save same shortcut key when prefix_key is null.
        if Label.objects.filter(suffix_key=attrs['suffix_key'],
                                prefix_key__isnull=True).exists():
            raise ValidationError('Duplicate key.')
        return super().validate(attrs)

    class Meta:
        model = Label
        fields = ('id', 'text', 'prefix_key', 'suffix_key', 'background_color', 'text_color')


class DocumentSerializer(serializers.ModelSerializer):
    annotations = serializers.SerializerMethodField()

    def get_annotations(self, instance):
        request = self.context.get('request')
        project = instance.project
        model = project.get_annotation_class()
        serializer = project.get_annotation_serializer()
        annotations = model.objects.filter(document=instance.id)
        if request:
            annotations = annotations.filter(user=request.user)
        serializer = serializer(annotations, many=True)
        return serializer.data

    class Meta:
        model = Document
        fields = ('id', 'text', 'annotations', 'meta')


class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'guideline', 'users', 'project_type', 'image', 'updated_at')
        read_only_fields = ('image', 'updated_at')


class TextClassificationProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = TextClassificationProject
        fields = ('id', 'name', 'description', 'guideline', 'users', 'project_type', 'image', 'updated_at')
        read_only_fields = ('image', 'updated_at', 'users')


class SequenceLabelingProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = SequenceLabelingProject
        fields = ('id', 'name', 'description', 'guideline', 'users', 'project_type', 'image', 'updated_at')
        read_only_fields = ('image', 'updated_at', 'users')


class Seq2seqProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Seq2seqProject
        fields = ('id', 'name', 'description', 'guideline', 'users', 'project_type', 'image', 'updated_at')
        read_only_fields = ('image', 'updated_at', 'users')


class ProjectPolymorphicSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        Project: ProjectSerializer,
        TextClassificationProject: TextClassificationProjectSerializer,
        SequenceLabelingProject: SequenceLabelingProjectSerializer,
        Seq2seqProject: Seq2seqProjectSerializer
    }


class ProjectFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        view = self.context.get('view', None)
        request = self.context.get('request', None)
        queryset = super(ProjectFilteredPrimaryKeyRelatedField, self).get_queryset()
        if not request or not queryset or not view:
            return None
        return queryset.filter(project=view.kwargs['project_id'])


class DocumentAnnotationSerializer(serializers.ModelSerializer):
    # label = ProjectFilteredPrimaryKeyRelatedField(queryset=Label.objects.all())
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all())
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = DocumentAnnotation
        fields = ('id', 'prob', 'label', 'user', 'document')
        read_only_fields = ('user', )


class SequenceAnnotationSerializer(serializers.ModelSerializer):
    #label = ProjectFilteredPrimaryKeyRelatedField(queryset=Label.objects.all())
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all())
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = SequenceAnnotation
        fields = ('id', 'prob', 'label', 'start_offset', 'end_offset', 'user', 'document')
        read_only_fields = ('user',)


class Seq2seqAnnotationSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = Seq2seqAnnotation
        fields = ('id', 'text', 'user', 'document')
        read_only_fields = ('user',)
