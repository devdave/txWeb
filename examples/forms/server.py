from pathlib import Path
import sys

from twisted.python.log import startLogging
from twisted.internet import reactor

from txweb import Texas
from txweb.lib.str_request import StrRequest
from txweb.util.reloader import reloader

HERE = Path(__file__).parent
PORT = 7070
HOST = "127.0.0.1"

app = Texas(__name__)



app.add_file("/", HERE / "main.html")


@app.route("/simple", methods=["GET"])
def simple_form(request: StrRequest):
    form_fields = list(request.args.items())

    # Note that for scenarios where a form has multiple inputs with the same name.
    check_box = request.args.getlist("check_field")

    return f"""
    URL: {request.uri}<br>
    Arguments:<br>
        {repr(form_fields)}<br>
    Check field:<br>
        {repr(check_box)}<br>
    """

@app.route("/simple_posted_form", methods=["post"])
def simple_posted(request: StrRequest):
    """
        Not the difference of using texas.form versus texas.args

        The reason is that form's that use GET, append their values to the submitting
         URL like /my_resource?text_field=blah&check_field=1&check_field=2

         so .args is for URL arguments.

         while POST'd forms send the form field in the response body.

    :param request:
    :return:
    """
    form_fields = list(request.form.items())

    # Note that for scenarios where a form has multiple inputs with the same name.
    check_box = request.form.getlist("check_field")

    return f"""
    Arguments:
        {repr(form_fields)}
    Check field:
        {repr(check_box)}
    """

@app.route("/file_upload", methods=["POST"])
def file_upload(request: StrRequest):

    uploaded_file = request.files.get("upload")

    file_name = uploaded_file.filename
    field_name = uploaded_file.name
    try:
        file = uploaded_file.stream.read().decode("utf-8")
    except UnicodeDecodeError:
        file = "Unable to decode file to UTF-8"

    file_type = uploaded_file.content_type

    return f"""    
            Field Name: {field_name}<br>
            Source file name: {file_name}<br>             
            File type: {file_type}<br>
            <br>            
            Uploaded file: <br>
            <pre>{file}</pre>    
    """



def main():

    startLogging(sys.stdout)
    app.listenTCP(PORT, HOST)

    print(f"Hosting on http://{HOST}:{PORT}/")

    reactor.run()


if __name__ == "__main__":
    reloader(main)