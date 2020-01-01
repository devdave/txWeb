
DEFAULT_BODY = \
b"""
<html>
    <head>
        <title>Ooops</title>
    </head>
    <body>
        <h1>{detail} - {code}</h1>
    </body>        
</html>
"""

ERROR_BODY = \
b"""
<html>
    <head>
        <title>Ooops</title>
    </head>
    <body>
        <div name="content">
        {content}
        </div>
    </body>        
</html>
"""

ERROR_CONTENT = \
"""
    <div>{digest}</div>
    {error_list}
"""

ERROR_LIST = \
"""
    <ol name="traceback">
    {error_items}
    </ol>
"""

ERROR_ITEM = \
"""
        <li class="traceback">
            <div class="location">{file_path}:{line_no}</div>
            <div class="detail">{detail}</div>
        </li>
"""