from app.views import app


@app.template_filter('strftimedelta')
def _strftimedelta(td):
    seconds = td.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours} h {minutes} min"
    else:
        return f"{minutes} min"
