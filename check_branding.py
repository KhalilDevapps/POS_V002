from app import db, Branding, app

# Check and update branding settings
with app.app_context():
    branding = Branding.query.first()
    if branding:
        print(f"BEFORE UPDATE:")
        print(f"Currency Symbol: {branding.currency_symbol}")
        print(f"Business Name: {branding.business_name}")
        print(f"App Name: {branding.app_name}")

        # Update currency symbol to AFA
        branding.currency_symbol = 'AFA'
        db.session.commit()

        print(f"\nAFTER UPDATE:")
        print(f"Currency Symbol: {branding.currency_symbol}")
        print("✅ Currency updated to AFA")
    else:
        print("No branding settings found")
