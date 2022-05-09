#!/Applications/Xcode.app/Contents/Developer/usr/bin/python3
# !/usr/local/bin/python3
import json
import sys
from tkinter import W


def write_inherited_methods(methods, h):
    for method in methods:
        if method["type"].startswith("virtual"):
            if "pure" in method and method["pure"]:
                # required
                optional = ""
            else:
                h.write("    // This is optionally overridden\n")
                optional = "// "

            if "args" in method:
                args = ",".join([arg["type"] + " " + arg["name"]
                                for arg in method["args"]])
            else:
                args = ""

            h.write("        {3}{0} {1} ({2}) override;\n".format(
                method["type"], method["name"], args, optional))


def write_methods(methods, h):
    for method in methods:
        pure = ""
        if "pure" in method and method["pure"]:
            pure = "= 0"
        if "args" in method:
            args = ",".join([arg["type"] + " " + arg["name"]
                            for arg in method["args"]])
        else:
            args = ""

        h.write("        {0} {1} ({2}) {3};\n".format(
            method["type"], method["name"], args, pure))


def write_fields(fields, h):
    for field in fields:
        h.write("        " + field["type"] + " " + field["name"] + ";\n")


def create_code(config, header, source):
    """
    Create the code from the configuration and the header and source.
    """
    # I think cpp always defaults to private for clasess
    current_scope = "private"
    with open(config, 'r') as f:
        data = json.load(f)

        filename = data["name"] + ".h"
        with open(filename, 'w') as h:
            h.write("#ifndef " + data["name"].upper() + "_H\n")
            h.write("#define " + data["name"].upper() + "_H\n")
            for include in data["includes"]:
                # we should find a better way to do this
                if "<" in include:
                    h.write("#include " + include + "\n")
                else:
                    h.write("#include \"" + include + "\"\n")
            h.write("\n")

            if "parent" in data:
                # should we check if the parent is already included?
                h.write("class " + data["name"] +
                        ": public " + data["parent"] + "\n{\n")
            else:
                h.write("class " + data["name"] + "\n{\n")
            h.write("    public:\n")
            current_scope = "public"
            # let's keep it simple for now and always have a constructor and
            # a virtual destructor that can be overriden to free memory
            h.write("        " + data["name"] + "();\n")
            h.write("        virtual ~" + data["name"] + "();\n")
            h.write("\n")

            # write the methods
            if "methods" in data:
                if "public" in data["methods"]:
                    if current_scope != "public" and len(data["methods"]["public"]) > 0:
                        h.write("    public:\n")
                        current_scope = "public"
                    write_methods(data["methods"]["public"], h)

                if "protected" in data["methods"]:
                    if current_scope != "protected" and len(data["methods"]["protected"]) > 0:
                        h.write("    protected:\n")
                        current_scope = "protected"
                    write_methods(data["methods"]["protected"], h)

                if "private" in data["methods"]:
                    if current_scope != "private" and len(data["methods"]["private"]) > 0:
                        h.write("    private:\n")
                        current_scope = "private"
                    write_methods(data["methods"]["private"], h)

            # read in parent class pure virtual methods
            if "parent" in data:
                # let's optional the virtual functions
                # and define the pure virtual functions
                with open(data["parent"] + ".json", 'r') as p:
                    parent = json.load(p)
                    print("Yes this is derived")
                    if "methods" in parent:
                        if "public" in parent["methods"]:
                            write_inherited_methods(
                                parent["methods"]["public"], h)
                        if "protected" in parent["methods"]:
                            write_inherited_methods(
                                parent["methods"]["protected"], h)

            # write the fields
            if "fields" in data:
                if "public" in data["fields"]:
                    if current_scope != "public" and len(data["fields"]["public"]) > 0:
                        h.write("    public:\n")
                        current_scope = "public"
                    write_fields(data["fields"]["public"], h)

                if "protected" in data["fields"]:
                    if current_scope != "protected" and len(data["fields"]["protected"]) > 0:
                        h.write("    protected:\n")
                        current_scope = "protected"
                    write_fields(data["fields"]["protected"], h)

                if "private" in data["fields"]:
                    if current_scope != "private" and len(data["fields"]["private"]) > 0:
                        h.write("    private:\n")
                        current_scope = "private"
                    write_fields(data["fields"]["private"], h)

            h.write("};\n\n")
            h.write("#endif // " + data["name"].upper() + "_H\n")


if "__main__" == __name__:
    # later figure out how to parse prompts properly
    if len(sys.argv) < 4:
        print("Usage: create_code.py <json> <header template> <source template>")
        sys.exit(1)
    else:
        create_code(sys.argv[1], sys.argv[2], sys.argv[3])
