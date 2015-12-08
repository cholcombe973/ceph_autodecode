import os

__author__ = 'chris holcombe'
import CppHeaderParser

decoded_types = {'eversion_t': 'Eversion',
                 'pg_shard_t': 'unknown',
                 'hobject_t': 'HObject',
                 'utime_t': 'Utime',
                 'ECSubWrite': 'ECSubWrite',
                 'ECSubWriteReply': 'ECSubWriteReply',
                 'ECSubRead': 'ECSubRead',
                 'ECSubReadReply': 'ECSubReadReply',
                 'pg_history_t': 'PgHistory',
                 }
struct_mapping = {
    'uuid_d': 'Uuid',
    # '':'le_i8',
    'bool': 'u8',
    'shard_id_t': 'i8',
    '__u8': 'u8',
    '__s16': 'i16',
    '__u16': 'u16',
    '__le16': 'u16',
    'int32_t': 'i32',
    'uint32_t': 'u32',
    '__u32': 'u32',
    '__s32': 'u32',
    'loff_t': 'u64',
    'int64_t': 'i64',
    'uint64_t': 'u64',
    '__le64': 'u64',
    # '':'be_u16,
    'errorcode32_t': 'i32',
    'version_t': 'u64',
    'ceph_tid_t': 'u64',
    'epoch_t': 'u32',
    'std::string': '\'a &str',
    'string': '\'a &str',
}

nom_mapping = {
    'uuid_d': 'parse_fsid',
    # '':'le_i8',
    'bool': 'le_u8',
    '__u8': 'le_u8',
    'shard_id_t': 'le_i8',
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


class RustStruct(object):
    def __init__(self, name, members=None):
        if not members:
            members = {}
        self.name = name
        self.members = members


def add_unit_test(struct_name, parts):
    output = ["#[test]",
              "fn test_ceph_{}(){{".format(struct_name),
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


def add_struct(struct_name, public_properties):
    output = [
        "#[derive(Debug,Eq,PartialEq)]",
        "pub struct " + struct_name + "{"
    ]
    members = {}
    for line in public_properties:
        if line['name'] == 'HEAD_VERSION':
            continue
        elif line['name'] == 'COMPAT_VERSION':
            continue
        if line['type'] in struct_mapping:
            members[line['name']] = struct_mapping[line['type']]
            output.append("\tpub {}: {},".format(line['name'], struct_mapping[line['type']]))
        else:
            if line['name'] in decoded_types:
                output.append("\tpub {}: {},".format(line['name'], decoded_types[line['name']]))
            else:
                pass
                # output.append("\tpub {}: {},".format(line['name'], line['type']))
                # members[line['name']] = line['type']
    output.append("}")
    decoded = RustStruct(name=struct_name, members=members)
    # decoded_types.(decoded)
    return output


def add_impl(struct_name, public_properties):
    output = ["impl<'a> CephPrimitive<'a> for {}{{".format(struct_name),
              "\tfn read_from_wire(input: &'a [u8]) -> nom::IResult<&[u8], Self>{"]
    for i in public_properties:
        if i['name'] == 'HEAD_VERSION':
            output.append('\tlet head_version = ' + str(i['static']) + ";")
            pass
        elif i['name'] == 'COMPAT_VERSION':
            output.append('\tlet compat_version = ' + str(i['static']) + ";")
    output.append("\tchain!(input,")
    for line in public_properties:
        # print "line: " + str(line)
        ceph_type = line['type']
        if ceph_type == 'HEAD_VERSION':
            continue
        elif ceph_type == 'COMPAT_VERSION':
            continue

        if ceph_type.startswith('map'):
            ceph_type_map = split_map(ceph_type)
            if ceph_type_map[0] in decoded_types and ceph_type_map[1] in decoded_types:
                output.append("\t{}: HashMap<{},{}>,".format(
                    line['name'],
                    decoded_types[ceph_type_map[0]],
                    decoded_types[ceph_type_map[1]],
                ))
            else:
                print("Unknown map type: " + str(ceph_type))

        elif ceph_type.startswith('pair'):
            ceph_type_map = split_map(ceph_type)
            print("Unknown pair types: " + str(ceph_type_map))

        elif ceph_type.startswith('std::map'):
            ceph_type_map = split_map(ceph_type)
            if ceph_type_map[0] in decoded_types:
                output.append("\t{}: HashMap<{},{}>,".format(
                    line['name'],
                    decoded_types[ceph_type_map[0]],
                    decoded_types[ceph_type_map[1]]
                ))
            else:
                print("Unknown std::map type: " + str(ceph_type))

        elif ceph_type.startswith('vector'):
            ceph_type_vector = split_vector(ceph_type)
            if ceph_type_vector in nom_mapping:
                output.append("\t{}: count!({}, count),".format(line['name'], nom_mapping[ceph_type_vector]))
            else:
                print("Unknown vector type: " + str(ceph_type))

        elif ceph_type.startswith('list'):
            ceph_type_vector = split_vector(ceph_type)
            if ceph_type_vector in nom_mapping:
                output.append("\t{}: count!({},count)".format(line['name'], nom_mapping[ceph_type_vector]))
            else:
                print("Unknown list type: " + str(ceph_type))

        elif ceph_type in nom_mapping:
            output.append("\t\t" + line['name'] + ": " + nom_mapping[ceph_type] + " ~")
        else:
            if ceph_type in decoded_types:
                output.append("\t{}: {},".format(line['name'], decoded_types[ceph_type]))
            else:
                print("Unknown type line 207: '" + str(ceph_type) + "'")
            # resolved_parts = resolve_type(ceph_type=ceph_type)
            #    for resolved_part in resolved_parts:
            #        output.append(resolved_part + ": " + nom_mapping[resolved_part] + "~")
    output.append("\t\t||{")
    output.append("\t\t\t" + struct_name + "{")
    for line in public_properties:
        if line['name'] == 'HEAD_VERSION':
            continue
        elif line['name'] == 'COMPAT_VERSION':
            continue
        output.append("\t\t\t" + line['name'] + ": " + line['name'] + ",")
    output.append("\t\t}")
    output.append("\t})")
    output.append("}")
    output.append("\tfn write_to_wire(&self) -> Result<Vec<u8>, SerialError>{")
    output.append("\t\tlet mut buffer: Vec<u8> = Vec::new();")
    output.append("\t\treturn Ok(buffer);")
    output.append("\t}")
    output.append("}")
    return output


def decode_ceph_messages():
    prefix = '/home/chris/repos/ceph'
    extras = [
        "src/osd/ECMsgTypes.h",
        "src/osd/osd_types.h",
    ]
    headers = os.listdir(os.path.join(prefix, 'src/messages'))
    for header in headers:
        try:
            print("parsing " + header)
            cpp_header = CppHeaderParser.CppHeader(os.path.join(prefix, 'src/messages', header))
            try:
                for clazz in cpp_header.classes:
                    parts = cpp_header.classes[clazz]['properties']['public']
                    print("Decoding: " + str(clazz))
                    add_unit_test(struct_name=clazz, parts=parts)
                    for output in add_struct(struct_name=clazz, public_properties=parts):
                        print output
                    for output in add_impl(struct_name=clazz, public_properties=parts):
                        print output
            except AttributeError, a:
                print a
        except CppHeaderParser.CppParseError, e:
            print e

    # Parse the extra headers to get everything
    for extra in extras:
        try:
            print("parsing extra: " + extra)
            cpp_header = CppHeaderParser.CppHeader(os.path.join(prefix, extra))
            try:
                for clazz in cpp_header.classes:
                    parts = cpp_header.classes[clazz]['properties']['public']
                    print("Decoding: " + str(clazz))
                    add_unit_test(struct_name=clazz, parts=parts)
                    for output in add_struct(struct_name=clazz, public_properties=parts):
                        print output
                    for output in add_impl(struct_name=clazz, public_properties=parts):
                        print output
            except AttributeError, a:
                print a
        except CppHeaderParser.CppParseError, e:
            print e


if __name__ == '__main__':
    # for everything in src/messages/*.h decode them
    decode_ceph_messages()
