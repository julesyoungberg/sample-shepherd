from sample_shepherd.sync.elektron import parse_info, parse_ld, parse_project_ls, parse_sample_ls


def test_ld():
    out = "0: id: SYSTEM; name: computer\n1: id: 42; name: Elektron Digitakt II\n"
    devs = parse_ld(out)
    assert [(d.number, d.id, d.name) for d in devs] == [("0", "SYSTEM", "computer"), ("1", "42", "Elektron Digitakt II")]


def test_sample_ls_matches_elektroid_format():
    # "%c %10s %08x %s" (elektron_print_smplrw)
    lines = [
        f"D {'0B':>10} {0:08x} 01_KICKS",
        f"F {'4.05MiB':>10} {0x0bbc22bd:08x} BD 01 hard",
        f"F {'512B':>10} {0xDEADBEEF:08x} tiny",
        f"F {'?B':>10} {0:08x} unknown size",
        "garbage line",
    ]
    es = parse_sample_ls("\n".join(lines))
    assert [(e.kind, e.name) for e in es] == [("D", "01_KICKS"), ("F", "BD 01 hard"), ("F", "tiny"), ("F", "unknown size")]
    assert es[1].size == round(4.05 * 1024**2) and es[1].hash == "0bbc22bd"
    assert es[2].size == 512 and es[2].hash == "deadbeef"
    assert es[3].size is None


def test_project_ls_fixed_columns():
    # "%c %04x %d %d %*s %*s %-*s%s%s%s" (elektron_print_data), widths 10/10/32
    lines = [
        f"F {7:04x} 1 1 {'1.2MiB':>10} {'1':>10} {'MY SONG':<32}",
        f"F {7:04x} 1 1 {'800KiB':>10} {'12':>10} {'NEW PROJECT':<32} [ 120 BPM ]",
        f"F {7:04x} 0 0 {'':>10} {'13':>10} {'':<32}",
        f"D {0:04x} 0 0 {'':>10} {'':>10} {'folder':<32}",
    ]
    ps = parse_project_ls("\n".join(lines))
    assert [(p.slot, p.name, p.valid) for p in ps] == [("1", "MY SONG", True), ("12", "NEW PROJECT", True), ("13", "", False)]
    assert ps[0].size == round(1.2 * 1024**2) and ps[2].size is None


def test_info_filesystems():
    text = "Type: MIDI\nDevice name: Digitakt II\nFilesystems: data, project, sample, raw (CLI only)\n"
    info = parse_info(text)
    assert info["filesystems"] == ["data", "project", "sample", "raw"]
    assert info["device_name"] == "Digitakt II"


def test_project_ls_older_elektroid_format():
    # older releases: type index perms valid metadata size name (Elektroid README)
    text = "D  -1 0000 0 0         0B projects\nF   1 0012 1 1       160B KICK\nF  12 0012 1 1     1.5MiB MY SONG\n"
    ps = parse_project_ls(text)
    assert [(p.slot, p.name, p.size) for p in ps] == [("1", "KICK", 160), ("12", "MY SONG", round(1.5 * 1024**2))]


def test_sample_ls_readme_example():
    text = "D              0B 00000000 drum machines\nF       630.34KiB f8711cd9 saw\nF         1.29MiB 0bbc22bd square\n"
    es = parse_sample_ls(text)
    assert [(e.kind, e.name, e.hash) for e in es] == [("D", "drum machines", "00000000"), ("F", "saw", "f8711cd9"),
                                                     ("F", "square", "0bbc22bd")]
