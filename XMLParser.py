"""
Author: Gabriel Engberg
Date: 13-03-2025
Info: Module to parse XML data and transform it into a structured dictionary.
"""

import xml.etree.ElementTree as ET
import re


class XMLParser:
    """
    A class to parse XML data and transform it into a structured dictionary.
    Provides functionality to extract specific elements, remove keys, rename keys,
    and pretty-print the parsed data.
    """

    def __init__(self, xml_string, parent_elements=None):
        """
        Initialize the XMLParser with the given XML string.

        :param xml_string: The XML data as a string.
        :param parent_elements: A list of parent element names to extract from XML.
        """
        self.xml_string = xml_string
        self.parent_elements = parent_elements or ["header", "values"]
        self.parsed_data = self.parse_xml_to_dict()

    def strip_namespace(self, tag):
        """Removes the namespace from an XML tag."""
        return re.sub(r'\{.*?\}', '', tag)

    def parse_xml_to_dict(self):
        """
        Parses the specified parent elements from the XML and converts them into dictionaries.

        :return: A dictionary containing the extracted parent elements.
        """

        def parse_element(element):
            """Recursively parses an XML element and its children, stripping namespaces."""
            data = {}
            for child in element:
                tag = self.strip_namespace(child.tag)
                if len(child):  # If the element has children, recurse
                    data[tag] = parse_element(child)
                else:
                    data[tag] = child.text.strip() if child.text else ""
            return data

        root = ET.fromstring(self.xml_string)
        extracted_data = {}

        for parent in self.parent_elements:
            for elem in root.iter():  # Iterate over all elements to handle namespaced parents
                if self.strip_namespace(elem.tag) == parent:
                    extracted_data[parent] = parse_element(elem)
                    break

        return extracted_data

    def remove_keys(self, keys_to_remove):
        """
        Removes specified keys from the extracted data.

        :param keys_to_remove: A list of keys to remove from the dictionaries.
        """

        def recursive_remove(data):
            if isinstance(data, dict):
                return {
                    k: recursive_remove(v) for k, v in data.items() if k not in keys_to_remove
                }
            if isinstance(data, list):
                return [recursive_remove(item) for item in data]
            return data

        for parent in self.parsed_data:
            self.parsed_data[parent] = recursive_remove(self.parsed_data[parent])

    def flatten_nested_keys(self, nested_key="Name", value_key="Value"):
        """
        Converts specific dictionary structures where a key contains a nested key-value pair,
        making the nested key the new dictionary key.

        :param nested_key: The key that should be promoted to the dictionary key.
        :param value_key: The key whose value should be assigned to the new key.
        """

        def recursive_parse(data):
            if isinstance(data, dict):
                new_data = {}
                for k, v in data.items():
                    if isinstance(v, dict) and nested_key in v:
                        new_key = v.pop(nested_key)  # Extract the new key
                        if len(v) == 1 and value_key in v:  # Check if it's in the special format
                            new_data[new_key] = v[value_key]  # Convert to string format
                        else:
                            new_data[new_key] = v  # Use new_key as key with remaining dict
                    else:
                        new_data[k] = recursive_parse(v)
                return new_data
            if isinstance(data, list):
                return [recursive_parse(item) for item in data]
            return data

        for parent in self.parsed_data:
            self.parsed_data[parent] = recursive_parse(self.parsed_data[parent])

    def rename_keys(self, translation_map, casing=None):
        """
        Renames dictionary keys based on a mapping and applies an optional casing function.

        :param translation_map: A dictionary mapping old keys to new keys.
        :param casing: A callable function (e.g., str.capitalize) to modify key casing.
        """

        def apply_casing(key):
            return casing(key) if callable(casing) else key

        def recursive_translate(data):
            if isinstance(data, dict):
                return {
                    apply_casing(translation_map.get(k.lower(), k)): recursive_translate(v)
                    for k, v in data.items()
                }
            if isinstance(data, list):
                return [recursive_translate(item) for item in data]
            return data

        for parent in self.parsed_data:
            self.parsed_data[parent] = recursive_translate(self.parsed_data[parent])

    def print_pretty_dict(self, data=None, indent=0):
        """
        Pretty prints the dictionary structure with indentation.

        :param data: The data to print. Defaults to self.parsed_data if not provided.
        :param indent: The indentation level (used internally for recursion).
        """
        if data is None:
            for parent, content in self.parsed_data.items():
                print(f"{parent.capitalize()}:")
                self.print_pretty_dict(content, indent)
            return

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print("\t" * indent + f"- {key}:")
                    self.print_pretty_dict(value, indent + 1)
                else:
                    print("\t" * indent + f"- {key}: {value}")
        elif isinstance(data, list):
            for item in data:
                self.print_pretty_dict(item, indent)
        else:
            print("\t" * indent + f"- {data}")


if __name__ == "__main__":
    # Example XML string
    data = """<root xmlns="http://example.com">
        <header>
            <ntitle>Sample Title</ntitle>
            <date>2025-03-13</date>
            <meta>
                <author>John Doe</author>
                <version>1.0</version>
            </meta>
        </header>
        <values>
            <price>100</price>
            <quantity>5</quantity>
            <details>
                <Name>Discount Details</Name>
                <currency>USD</currency>
                <discount>10%</discount>
            </details>
            <extra>
                <Name>Special Offer</Name>
                <Value>50% Off</Value>
            </extra>
        </values>
    </root>"""

    # Using the class
    parser = XMLParser(data, parent_elements=["header", "values"])
    parser.remove_keys(["meta"])
    parser.flatten_nested_keys()
    parser.rename_keys(
        {"price": "cost", "quantity": "amount", "discount": "rebate"},
        casing=str.capitalize,
    )
    parser.print_pretty_dict()
