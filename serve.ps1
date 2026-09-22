$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:5000/")
$listener.Start()
Write-Output "Server listening on http://localhost:5000/"
while ($listener.IsListening) {
    $context = $listener.GetContext()
    $req = $context.Request
    $res = $context.Response
    
    $path = $req.Url.LocalPath.TrimStart('/')
    if ($path -eq "" -or $path -eq "index.html") { $path = "index.html" }
    
    $fullPath = Join-Path "c:\Users\kolga\OneDrive\Desktop\ANELProjects\analytics" $path
    if (Test-Path $fullPath -PathType Leaf) {
        $bytes = [System.IO.File]::ReadAllBytes($fullPath)
        if ($path.EndsWith(".html")) { $res.ContentType = "text/html; charset=utf-8" }
        elseif ($path.EndsWith(".css")) { $res.ContentType = "text/css; charset=utf-8" }
        elseif ($path.EndsWith(".js")) { $res.ContentType = "application/javascript; charset=utf-8" }
        elseif ($path.EndsWith(".json")) { $res.ContentType = "application/json; charset=utf-8" }
        $res.ContentLength64 = $bytes.Length
        $res.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
        $res.StatusCode = 404
    }
    $res.OutputStream.Close()
}
