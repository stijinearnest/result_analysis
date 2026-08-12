def role_flags(request):
    return {
        "is_hod_user": request.user.groups.filter(name="HOD").exists()
    }