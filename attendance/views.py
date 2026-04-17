from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.serializers import (
    CheckInByTokenResponseSerializer,
    CheckInByTokenSerializer,
)
from attendance.services import (
    AlreadyCheckedIn,
    CheckInNotAllowed,
    CheckInTokenNotFound,
    InvalidCheckInToken,
    check_in_by_token,
)


def _attendance_error_response(exc):
    if isinstance(exc, AlreadyCheckedIn):
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, CheckInNotAllowed):
        return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
    if isinstance(exc, InvalidCheckInToken):
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, CheckInTokenNotFound):
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class CheckInByTokenView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = CheckInByTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resolved = check_in_by_token(
                str(serializer.validated_data["token"]),
                actor=request.user,
                source=serializer.validated_data.get("source") or "manual",
                notes=serializer.validated_data.get("notes") or "",
            )
        except (
            AlreadyCheckedIn,
            CheckInNotAllowed,
            InvalidCheckInToken,
            CheckInTokenNotFound,
        ) as exc:
            return _attendance_error_response(exc)

        response = CheckInByTokenResponseSerializer(
            {
                "kind": resolved.kind,
                "id": resolved.instance.id,
                "checked_in_at": resolved.instance.checked_in_at,
            }
        )
        return Response(response.data, status=status.HTTP_200_OK)
