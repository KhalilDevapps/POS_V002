#!/usr/bin/env python3

from app import app, db, User

with app.app_context():
    # Get the admin user
    admin_user = User.query.filter_by(username='admin').first()

    if admin_user:
        print(f"Admin user found: {admin_user.username}")
        print(f"Role: {admin_user.role}")
        print(f"Permissions: {admin_user.get_permissions()}")

        # Check if admin has system_admin permission
        from app import has_permission
        has_admin_perm = has_permission(admin_user, 'system_admin')
        print(f"Has system_admin permission: {has_admin_perm}")

        # Check all available permissions
        from app import ROLE_PERMISSIONS
        print(f"\nRole permissions for '{admin_user.role}':")
        admin_permissions = ROLE_PERMISSIONS.get(admin_user.role, [])
        for perm in admin_permissions:
            print(f"  - {perm}")

    else:
        print("❌ Admin user not found")

    print("\nAll available roles and their permissions:")
    from app import ROLE_PERMISSIONS
    for role, perms in ROLE_PERMISSIONS.items():
        print(f"\n{role.upper()}:")
        for perm in perms:
            print(f"  - {perm}")
