# Use Inkscape to convert DXF to SVG by Python 3, and put everything inside a Docker container

## Objective
The primary purpose of this repo is to do a **POC (Proof of Concept)** of the following:

- Use the python script inside inkscape (`inkscape/usr/share/inkscape/extensions/dxf_input.py`) to convert DXF to SVG
- We want to make it a "web service", which means we hide everything inside a python script.  Developer just needs to provide necessary information to do the convertion.

## Main conversion workflow - Use Inkscape to do DXF to SVG
- Our conversion workflow is:
    - We get the `.dxf` file from AWS S3
    - Convert it using Inkscape
    - Putting it back to AWS S3 with same file name, with different extension (`.svg`), which means:
      - Source: `<s3_location>/my_file.dxf`
      - Target: `<s3_location>/my_file.svg`
    - In other words, **we just do the conversion inside docker container**, source and target files are **not permanently saved** in container.

## Full workflow - Accept HTTP request

1. User does HTTP POST to a URL (REST API)
   - AWS Public Key + Secret in HTTP Header
     - I know it is insecure if such info is exposed to public.  But since it is used only in internal environment, and only called by other server (Server to Server), so it is OK for me to do so.  Please adjust your workflow accordingly.
   - S3 repository name and S3 `.dxf` file location

2. We use python [Flask](https://flask.palletsprojects.com/en/2.0.x/) as REST API.  And [Waitress](https://docs.pylonsproject.org/projects/waitress/en/latest/) to act as server.
   - Run the Main conversion workflow above.
3. Return a JSON string to indicate success or not

## About Inkscape

### What is Inkscape
[Inkscape](https://inkscape.org/) is a graphic editing tool.  There are Linux and Windows versions.

### How are we going to use it?
We mainly use Linux version.  To be precise, we use the Python script inside Inkscape.

And interestingly (or Luckily?), **there is a python executable inside Inkscape**, which means, you don't need to install Python yourself, which may cause other weird errors.

Simply put, we use everything inside Inkscape to avoid any potential python conflict.

### Some notes on using Inkscape Linux version
If you download the Linux "Package" from their official site, you will see it is actually an Appimage, not a usual .tar.gz or rpm package.

Therefore, we need to extract the Appimage, and use the python **inside inkscape** to execute the python script **inside inkscape extension directory**.

## Dockerfile - How the infrastructure is constructed?
- We use Ubuntu latest version
- Expose/Open port 80, 443
- Install `Python3` and `pip`
  - It is **not** the python used to run inkscape.  This is use to run the API server (or called WSGI server)
- Use `boto3` to connect to AWS services
- Use `flask` as REST API framework
- Use `Waitress` as production web server
- Copy the Appimage downloaded from Inkscape.org to container
  - Download the Appimage from inkscape.org, put the file in the same directory as Dockerfile.  This is a bigger-than-100MB file, so I did not put it in this Git repo.
  - As you can see, the Inkscape AppImage name is `Inkscape-3bf5ae0-x86_64.AppImage` as of this writing.
  - In other words, when you are using this Dockerfile, chances are the AppImage file name is not this one.
  - Therefore, you need to edit this Dockerfile and update the Appimage name accordingly.
- Extract the Appimage: `./Inkscape-3bf5ae0-x86_64.AppImage --appimage-extract`
- Copy `app.py`, which is the main python script that accept web request to docker container
- Start Python Waitress server inside container and listen to 80, 443.
  - I make the max header size to 1MB.

## `app.py` - How does the conversion command work
- I would like to focus on the main command that convert `.dxf` to `.svg`.
- Please note: The path to `dxf_input.py` is different under Linux and Windows.
- As of this writing, the full path, after extract, is `squashfs-root/usr/share/inkscape/extensions/dxf_input.py`.
  - Yes you read that right: the top folder name after extracing AppImage is `squashfs-root`.
- Then all you need to do is running:
  - `/usr/bin/sh /root/squashfs-root/usr/bin/python /root/squashfs-root/usr/share/inkscape/extensions/dxf_input.py /root/__your_dxf_local_filename__ --output=/root/__your_target_svg_local_filename__ --scalemethod=auto`
  - Without `--scalemethod=auto`, you will only get part of the file.  Adjust to fit your situation.
  - You can always run `python dxf_input.py --help` in your local environment, or simply open that file to see what other params you can use.  This is a python script.