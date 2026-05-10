from zstar.utils import read_yaml_file


def test_read_yaml_file_returns_dict_from_yaml(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("backend:\n  host: 0.0.0.0\n  port: 9000\n", encoding="utf-8")

    data = read_yaml_file(config_path)

    assert data["backend"]["host"] == "0.0.0.0"
    assert data["backend"]["port"] == 9000


def test_read_yaml_file_returns_empty_dict_for_empty_file(tmp_path):
    config_path = tmp_path / "empty.yaml"
    config_path.write_text("", encoding="utf-8")

    data = read_yaml_file(config_path)

    assert data == {}
