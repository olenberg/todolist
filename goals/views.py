from django.db import transaction
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from goals.models import GoalCategory, Goal, GoalComment, Board, BoardParticipant
from goals.serializers import GoalCategoryCreateSerializer, GoalCategorySerializer, GoalCreateSerializer, GoalSerializer,\
    GoalCommentCreateSerializer, GoalCommentSerializer, BoardCreateSerializer, BoardParticipantSerializer, \
    BoardSerializer, BoardListSerializer
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from goals.filters import GoalDateFilter
from goals.permissions import GoalCategoryPermission, GoalPermission, CommentPermission, BoardPermission
from rest_framework.permissions import IsAuthenticated


class GoalCategoryCreateView(CreateAPIView):
    model = GoalCategory
    permission_classes = [IsAuthenticated]
    serializer_class = GoalCategoryCreateSerializer


class GoalCategoryListView(ListAPIView):
    model = GoalCategory
    permission_classes = [IsAuthenticated]
    serializer_class = GoalCategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    ordering_fields = ["title", "created"]
    ordering = ["title"]
    search_fields = ["title"]

    def get_queryset(self):
        return GoalCategory.objects.filter(board__participants__user=self.request.user).exclude(is_deleted=True)


class GoalCategoryView(RetrieveUpdateDestroyAPIView):
    model = GoalCategory
    serializer_class = GoalCategorySerializer
    permission_classes = [GoalCategoryPermission]

    def get_queryset(self):
        return GoalCategory.objects.filter(board__participants__user=self.request.user).exclude(is_deleted=True)

    def perform_destroy(self, instance:GoalCategory):
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            Goal.objects.filter(category=instance).update(status=Goal.Status.archived)


class GoalCreateView(CreateAPIView):
    model = Goal
    permission_classes = [IsAuthenticated]
    serializer_class = GoalCreateSerializer


class GoalListView(ListAPIView):
    model = Goal
    permission_classes = [IsAuthenticated]
    serializer_class = GoalSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = GoalDateFilter
    search_fields = ["title", "description"]
    ordering_fields = ["priority", "due_date"]
    ordering = ["priority", "due_date"]

    def get_queryset(self):
        return Goal.objects.filter(category__board__participants__user=self.request.user)


class GoalView(RetrieveUpdateDestroyAPIView):
    model = Goal
    permission_classes = [GoalPermission]
    serializer_class = GoalSerializer

    def get_queryset(self):
        return Goal.objects.filter(category__board__participants__user=self.request.user)

    def perform_destroy(self, instance):
        instance.status = Goal.Status.archived
        instance.save(update_fields=('status',))


class GoalCommentCreateView(CreateAPIView):
    model = GoalComment
    serializer_class = GoalCommentCreateSerializer
    permission_classes = [IsAuthenticated]


class GoalCommentListView(ListAPIView):
    serializer_class = GoalCommentSerializer
    permission_classes = [IsAuthenticated]
    # pagination_class = LimitOffsetPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    # ordering_fields = ["text", "created"]
    filterset_fields = ['goal']
    ordering = ["-created"]

    def get_queryset(self):
        return GoalComment.objects.filter(goal__category__board__participants__user=self.request.user)


class CommentView(RetrieveUpdateDestroyAPIView):
    model = GoalComment
    serializer_class = GoalCommentSerializer
    permission_classes = [CommentPermission]

    def get_queryset(self):
        return GoalComment.objects.filter(goal__category__board__participants__user=self.request.user)


class BoardCreateView(CreateAPIView):
    model = Board
    permission_classes = [BoardPermission]
    serializer_class = BoardCreateSerializer


class BoardListView(ListAPIView):
    model = Board
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination
    serializer_class = BoardListSerializer
    filter_backends = [OrderingFilter]
    ordering = ["title"]

    def get_queryset(self):
        return Board.objects.filter(participants__user=self.request.user, is_deleted=False)


class BoardView(RetrieveUpdateDestroyAPIView):
    model = Board
    serializer_class = BoardSerializer
    permission_classes = [BoardPermission]

    def get_queryset(self):
        return Board.objects.filter(participants__user=self.request.user, is_deleted=False)

    def perform_destroy(self, instance: Board):
        with transaction.atomic():
            instance.is_deleted = True
            instance.save()
            instance.categories.update(is_deleted=True)
            Goal.objects.filter(category__board=instance).update(status=Goal.Status.archived)
