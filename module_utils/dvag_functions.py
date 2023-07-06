import yaml

def struct_to_yaml(struct):

    def should_use_block(value):
        for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
            if c in value:
                return True
        return False

    def my_represent_scalar(self, tag, value, style=None):
        if style is None:
            if should_use_block(value):
                style='|'
            else:
                style = self.default_style

        node = yaml.representer.ScalarNode(tag, value, style=style)
        return node

    yaml.representer.BaseRepresenter.represent_scalar = my_represent_scalar

    return yaml.dump(struct, allow_unicode=True, default_flow_style=False)
