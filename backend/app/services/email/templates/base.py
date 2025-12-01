"""
Base HTML email template with modern, responsive design.
"""

def get_base_template(
    title: str,
    preview_text: str,
    content_html: str,
    footer_text: str | None = None,
    app_name: str | None = None,
    app_description: str | None = None,
) -> str:
    """
    Get base email template with consistent styling.
    
    Args:
        title: Email title/subject
        preview_text: Preview text shown in email clients
        content_html: Main content HTML
        footer_text: Footer text (defaults to branded tagline)
        app_name: Optional app name override
        app_description: Optional description override
        
    Returns:
        Complete HTML email string
    """
    resolved_app_name = app_name or "RAG Fortress"
    resolved_description = app_description or "Secure document intelligence platform"
    resolved_footer = footer_text or f"{resolved_app_name} — {resolved_description}"
    return f"""<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="utf-8">
    <meta name="x-apple-disable-message-reformatting">
    <meta http-equiv="x-ua-compatible" content="ie=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="format-detection" content="telephone=no, date=no, address=no, email=no">
    <title>{title}</title>
    <!--[if mso]>
    <xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
    <![endif]-->
    <style>
        /* Reset styles */
        body, table, td, a {{ text-decoration: none; }}
        img {{ border: 0; outline: none; }}
        
        /* Base styles */
        body {{
            margin: 0;
            padding: 0;
            width: 100%;
            word-break: break-word;
            -webkit-font-smoothing: antialiased;
            background-color: #f6f9fc;
        }}
        
        /* Responsive */
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .content {{ padding: 20px !important; }}
            .button {{ width: 100% !important; }}
        }}
        
        /* Typography */
        .heading {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 24px;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0 0 20px 0;
            line-height: 1.3;
        }}
        
        .text {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            color: #4a5568;
            line-height: 1.6;
            margin: 0 0 16px 0;
        }}
        
        /* Button */
        .button {{
            display: inline-block;
            padding: 16px 32px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            font-weight: 600;
            color: #ffffff !important;
            background-color: #4f46e5;
            border-radius: 8px;
            text-decoration: none;
            transition: background-color 0.2s;
        }}
        
        .button:hover {{
            background-color: #4338ca;
        }}
        
        /* Card */
        .card {{
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            overflow: hidden;
        }}
        
        /* Footer */
        .footer {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            color: #718096;
            text-align: center;
            padding: 32px 20px;
        }}
        
        .footer-link {{
            color: #4f46e5;
            text-decoration: none;
        }}

        .tagline {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            color: #94a3b8;
            margin: 8px 0 0 0;
        }}
        
        /* Divider */
        .divider {{
            height: 1px;
            background-color: #e2e8f0;
            margin: 32px 0;
        }}
        
        /* Logo */
        .logo {{
            font-size: 28px;
            font-weight: 700;
            color: #4f46e5;
            text-decoration: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
    </style>
</head>
<body>
    <!-- Preview text -->
    <div style="display: none; max-height: 0; overflow: hidden;">
        {preview_text}
    </div>
    
    <!-- Spacer -->
    <div style="display: none; max-height: 0px; overflow: hidden;">
        &nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌&nbsp;‌
    </div>
    
    <!-- Email wrapper -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f6f9fc;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Container -->
                <table class="container" role="presentation" width="600" cellpadding="0" cellspacing="0">
                    <!-- Logo header -->
                    <tr>
                        <td style="padding-bottom: 32px; text-align: center;">
                            <a href="#" class="logo" style="text-decoration: none;">
                                🏰 {resolved_app_name}
                            </a>
                            <p class="tagline">{resolved_description}</p>
                        </td>
                    </tr>
                    
                    <!-- Main card -->
                    <tr>
                        <td>
                            <table class="card" role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td class="content" style="padding: 48px 40px;">
                                        {content_html}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td class="footer">
                            <p style="margin: 0 0 8px 0;">{resolved_footer}</p>
                            <p style="margin: 0;">
                                <a href="#" class="footer-link">Privacy Policy</a> •
                                <a href="#" class="footer-link">Terms of Service</a> •
                                <a href="#" class="footer-link">Help Center</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
