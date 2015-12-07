import os

__author__ = 'chris'
import CppHeaderParser

decoded_types = []

nom_mapping = {
    'uuid_d': 'fsid',
    # '':'le_i8',
    'bool': 'le_u8',
    '__u8': 'le_u8',
    '__s16': 'le_i16',
    '__u16': 'le_u16',
    '__le16': 'le_u16',
    'int32_t': 'le_i32',
    'uint32_t': 'le_u32',
    '__u32': 'le_u32',
    '__s32': 'le_u32',
    'loff_t': 'le_u64',
    'int64_t': 'le_i64',
    'uint64_t': 'le_u64',
    '__le64': 'le_u64',
    # '':'be_u16,
    'errorcode32_t': 'le_i32',
    'version_t': 'le_u64',
    'ceph_tid_t': 'le_u64',
    'epoch_t': 'le_u32',
    'std::string': 'parse_str',
    'string': 'parse_str',
}


def add_unit_test(struct_name, parts):
    output = ["#[test]",
              "fn test_ceph_connect_reply(){",
              "let bytes = vec![", "];",
              "let x: &[u8] = &[];",
              "let expected_result = {} {{".format(struct_name),
              "};",
              "let result = {}::read_from_wire(&bytes);".format(struct_name),
              "println!(\"ceph_connect_reply: {:?}\", result);",
              "assert_eq!(Done(x, expected_result), result);",
              "}"]
    return output


def resolve_type(ceph_type):
    print("Unknown type: " + ceph_type)
    output = []
    return output


def split_map(ceph_map):
    if ceph_map.startswith('std::map'):
        parts = ceph_map.strip('std::map<').rstrip('>').split(',')
        return parts[0].strip(), parts[1].strip()

    elif ceph_map.startswith('pair'):
        parts = ceph_map.strip('pair<').rstrip('>').split(',')
        return parts[0].strip(), parts[1].strip()
    else:
        parts = ceph_map.strip('map<').rstrip('>').split(',')
        return parts[0].strip(), parts[1].strip()


def split_vector(ceph_vector):
    if ceph_vector.startswith('list'):
        return ceph_vector.strip('list<').rstrip('>').strip()
    elif ceph_vector.startswith('std::vector'):
        return ceph_vector.strip('std::vector<').rstrip('>').strip()
    else:
        return ceph_vector.strip('vector<').rstrip('>').strip()


def add_impl(struct_name, public_properties):
    output = ["impl<'a> CephPrimitive<'a> for {}{{\n".format(struct_name),
              "fn read_from_wire(input: &'a [u8]) -> nom::IResult<&[u8], Self>{\n",
              "\tchain!(input,\n"]
    for line in public_properties:
        print "line: " + str(line)
        ceph_type = line['type']

        if ceph_type.startswith('map'):
            ceph_type_map = split_map(ceph_type)
            print("Unknown types: " + str(ceph_type_map))

        elif ceph_type.startswith('pair'):
            ceph_type_map = split_map(ceph_type)
            print("Unknown types: " + str(ceph_type_map))

        elif ceph_type.startswith('std::map'):
            ceph_type_map = split_map(ceph_type)
            print("Unknown types: " + str(ceph_type_map))

        elif ceph_type.startswith('vector'):
            ceph_type_vector = split_vector(ceph_type)
            print("Unknown type: " + str(ceph_type_vector))

        elif ceph_type.startswith('list'):
            ceph_type_vector = split_vector(ceph_type)
            print("Unknown type: " + str(ceph_type_vector))

        elif ceph_type in nom_mapping:
            output.append(line['name'] + ": " + nom_mapping[ceph_type] + "~\n")
        else:
            print("Unknown type: " + str(ceph_type))
            #    resolved_parts = resolve_type(ceph_type=line.type)
            #    for resolved_part in resolved_parts:
            #        output.append(resolved_part + ": " + nom_mapping[resolved_part] + "~")
    output.append("\t\t||{\n")
    output.append(struct_name + "{\n")
    for line in public_properties:
        output.append(line['name'] + ": " + line['name'] + ",\n")
    output.append("}\n")
    output.append("}\n")
    output.append(")\n")
    output.append("}\n")
    output.append("fn write_to_wire(&self) -> Result<Vec<u8>, SerialError>{\n")
    output.append("let mut buffer: Vec<u8> = Vec::new();\n")
    output.append("return Ok(buffer);\n")
    output.append("}\n")
    output.append("}\n")
    return output


def decode_ceph_messages():
    prefix = '/home/chris/repos/ceph/src/messages'
    headers = os.listdir(prefix)
    for header in headers:
        try:
            print("parsing " + header)
            cpp_header = CppHeaderParser.CppHeader(os.path.join(prefix, header))
            try:
                for clazz in cpp_header.classes:
                    parts = cpp_header.classes[clazz]['properties']['public']
                    print("Decoding: " + str(clazz))
                    add_unit_test(struct_name=clazz, parts=parts)
                    for output in add_impl(struct_name=clazz, public_properties=parts):
                        print output
            except AttributeError, a:
                print a
        except CppHeaderParser.CppParseError, e:
            print e


if __name__ == '__main__':
    # for everything in src/messages/*.h decode them
    decode_ceph_messages()
