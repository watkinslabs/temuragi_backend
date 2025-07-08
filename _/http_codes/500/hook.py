from flask import render_template


def register_broken_code_error_handlers(app):
    """Register site-wide error handlers from this submodule."""
    
    @app.errorhandler(500)
    def handle_500_error(error):
        import traceback
        import sys
        from flask import render_template, jsonify, request
        
        error_info = {
            "error_type": sys.exc_info()[0].__name__ if sys.exc_info()[0] else "Unknown",
            "error_message": str(sys.exc_info()[1]),
            "error_traceback": traceback.format_exc()
        }
        
        if "application/json" in request.headers.get("Accept", ""):
            return jsonify(error_info), 500
        else:
            return render_template("500/500.html", error_info=error_info), 500
    
    return app