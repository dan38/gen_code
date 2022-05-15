#!/Applications/Xcode.app/Contents/Developer/usr/bin/python3
# !/usr/local/bin/python3
import json
import sys
from tkinter import W


def write_inherited_method_declarations(methods, h):
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


def write_inherited_method_outline(class_name, methods, cpp):
    for method in methods:
        if method["type"].startswith("virtual"):
            if "pure" in method and method["pure"]:
                # required
                pass
            else:
                cpp.write("    // This is optionally overridden\n")

            if "args" in method:
                args = ",".join([arg["type"] + " " + arg["name"]
                                for arg in method["args"]])
            else:
                args = ""

            cpp.write("{0} {3}::{1} ({2})\n".format(
                method["type"], method["name"], args, class_name))
            # maybe someday the methods can have information on implementation?
            cpp.write("{\n}\n\n")


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


def create_header(data):
    header_filename = data["name"] + ".h"
    with open(header_filename, 'w') as h:
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
                        write_inherited_method_declarations(
                            parent["methods"]["public"], h)
                    if "protected" in parent["methods"]:
                        write_inherited_method_declarations(
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


def initialize_value(dataType):
    if dataType == "int":
        return "0"
    elif dataType == "std::string":
        return '""'
    elif dataType == "string":
        return '""'
    else:
        return "nullptr /* {0} */".format(dataType)


def initializers(fields):
    vars = ["{0}({1})".format(
        field["name"], initialize_value(field["type"])) for field in fields]

    return vars


def create_source(data):
    source_filename = data["name"] + ".cpp"
    with open(source_filename, 'w') as c_file:
        c_file.write("#include \"" + data["name"] + ".h\"\n\n")

        init_str = ""
        init_list = []
        if "fields" in data:
            for scope in ["public", "protected", "private"]:
                if scope in data["fields"]:
                    init_list.extend(initializers(data["fields"][scope]))

        if len(init_list) > 0:
            init_str = ":" + " ".join(init_list)

        # constructor
        c_file.write("{0}::{0}(){1}\n".format(data["name"], init_str))
        c_file.write("{\n}\n\n")

        # destructor
        c_file.write("{0}::~{0}()\n".format(data["name"]))
        c_file.write("{\n}\n\n")

        # read in parent class pure virtual methods
        if "parent" in data:
            # let's optional the virtual functions
            # and define the pure virtual functions
            with open(data["parent"] + ".json", 'r') as p:
                parent = json.load(p)
                print("Yes this is derived")
                if "methods" in parent:
                    if "public" in parent["methods"]:
                        write_inherited_method_outline(data["name"],
                                                       parent["methods"]["public"], c_file)
                    if "protected" in parent["methods"]:
                        write_inherited_method_outline(data["name"],
                                                       parent["methods"]["protected"], c_file)


def create_code(config, header, source):
    """
    Create the code from the configuration and the header and source.
    """
    # I think cpp always defaults to private for clasess
    current_scope = "private"
    with open(config, 'r') as f:
        data = json.load(f)
        create_header(data)
        create_source(data)


if "__main__" == __name__:
    # later figure out how to parse prompts properly
    if len(sys.argv) < 4:
        print("Usage: create_code.py <json> <header template> <source template>")
        sys.exit(1)
    else:
        create_code(sys.argv[1], sys.argv[2], sys.argv[3])
