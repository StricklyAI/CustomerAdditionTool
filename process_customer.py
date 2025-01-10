import pandas as pd
import yaml
import os
import ipaddress
import logging
from tqdm import tqdm
import re

# Set up logging to track the script's actions and errors
logging.basicConfig(
    filename='customer_processing.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Convert subnet mask to CIDR notation (e.g., 255.255.255.0 -> 24)
def subnet_mask_to_cidr(subnet_mask):
    try:
        if '/' in subnet_mask:
            cidr = int(subnet_mask.lstrip('/'))
            if not 0 <= cidr <= 32:
                raise ValueError("Invalid CIDR range. Must be between /0 and /32.")
            return cidr
        else:
            return ipaddress.IPv4Network(f"0.0.0.0/{subnet_mask}").prefixlen
    except ValueError as e:
        logging.error(f"Invalid subnet mask or CIDR: {subnet_mask} - {e}")
        raise

# Convert CIDR notation to a standard subnet mask (e.g., /24 -> 255.255.255.0)
def cidr_to_subnet_mask(cidr):
    try:
        network = ipaddress.IPv4Network(f"0.0.0.0/{cidr}")
        return str(network.netmask)
    except ValueError as e:
        logging.error(f"Invalid CIDR notation: {cidr} - {e}")
        raise

# Generate an object name in the format CustomerName_IPAddress_CIDR
def generate_object_name(name, ip_address, subnet_mask):
    cidr = subnet_mask_to_cidr(subnet_mask)
    return f"{name}_{ip_address}_{cidr}"

# Validate IP address
def validate_ip_address(ip_address):
    try:
        ipaddress.IPv4Address(ip_address)
        return True
    except ipaddress.AddressValueError:
        print(f"Invalid IP address: {ip_address}. Please enter a valid IPv4 address.")
        return False

# Validate subnet mask
def validate_subnet_mask(subnet_mask):
    try:
        if '/' in subnet_mask:
            cidr = int(subnet_mask.lstrip('/'))
            if 0 <= cidr <= 32:
                return True
        else:
            ipaddress.IPv4Network(f"0.0.0.0/{subnet_mask}")
            return True
    except ValueError:
        print(f"Invalid subnet mask: {subnet_mask}. Please enter a valid subnet mask (e.g., 255.255.255.0 or /24).")
        return False

# Validate tags (ASCII alphanumeric, underscores, and dashes only)
def validate_tags(tags):
    pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    valid_tags = []
    for tag in tags.split(','):
        tag = tag.strip()
        if tag and pattern.fullmatch(tag):
            valid_tags.append(tag)
        elif tag:
            print(f"Invalid tag: {tag}. Only alphanumeric characters, underscores, and dashes are allowed with no spaces.")
    return valid_tags

# Load customer data from file
def load_customer_file():
    while True:
        file_path = input("Enter the path to the Excel or CSV file: ").strip()
        if os.path.exists(file_path):
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path).to_dict(orient='records')
            elif file_path.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file_path).to_dict(orient='records')
            else:
                print("Unsupported file format. Please provide a CSV or Excel file.")
        else:
            print("File not found.")
            choice = input("Would you like to enter the data manually instead? (y/n): ").strip().lower()
            if choice == 'y':
                return collect_manual_input()

# Collect manual input from the user
def collect_manual_input():
    customers = []
    print("\nEntering manual input mode. Enter customer details. Type 'done' when finished.\n")

    while True:
        name = input("Enter Customer Name (or type 'done' to finish): ").strip()
        if name.lower() == 'done':
            break

        ip_address = input("Enter Customer IP Address: ").strip()
        while not validate_ip_address(ip_address):
            ip_address = input("Please enter a valid Customer IP Address: ").strip()

        subnet_mask = input("Enter IP Subnet Mask (e.g., 255.255.255.0 or /24): ").strip()
        while not validate_subnet_mask(subnet_mask):
            subnet_mask = input("Please enter a valid IP Subnet Mask (e.g., 255.255.255.0 or /24): ").strip()

        tags = input("Enter Tags (comma-separated, or leave blank for none): ").strip()
        valid_tags = validate_tags(tags)

        object_name = generate_object_name(name, ip_address, subnet_mask)

        customers.append({
            'CustomerName': name,
            'CustomerIPAddress': ip_address,
            'IPSubnetMask': subnet_mask,
            'Tags': valid_tags,
            'ObjectName': object_name
        })

    return customers

# Function to allow the user to preview, edit, or delete customer data
def preview_and_edit(customers):
    print("\nPreviewing customer data...")
    deleted_customers = []

    index = 0
    while index < len(customers):
        customer = customers[index]
        print(f"\nCustomer {index + 1}:")
        for key, value in customer.items():
            print(f"  {key}: {value}")

        action = input("\nDo you want to edit or delete this customer? (e = edit, d = delete, n = next): ").strip().lower()

        if action == 'e':
            customer['CustomerName'] = input("Enter new Customer Name (leave blank to keep current): ").strip() or customer['CustomerName']
            customer['CustomerIPAddress'] = input("Enter new Customer IP Address (leave blank to keep current): ").strip() or customer['CustomerIPAddress']
            new_subnet_mask = input("Enter new IP Subnet Mask (leave blank to keep current): ").strip()
            if new_subnet_mask:
                customer['IPSubnetMask'] = new_subnet_mask
            new_tags = input("Enter new Tags (comma-separated, leave blank to keep current): ").strip()
            customer['Tags'] = validate_tags(new_tags) if new_tags else customer['Tags']
            customer['ObjectName'] = generate_object_name(customer['CustomerName'], customer['CustomerIPAddress'], customer['IPSubnetMask'])

        elif action == 'd':
            confirm = input("Are you sure you want to delete this customer? (y/n): ").strip().lower()
            if confirm == 'y':
                deleted_customer = customers.pop(index)
                deleted_customers.append((index, deleted_customer))
                print("Customer deleted.")

                undo = input("Do you want to undo this deletion? (y/n): ").strip().lower()
                if undo == 'y':
                    customers.insert(index, deleted_customer)
                    print("Deletion undone.")
                    continue

        index += 1

    return customers

# Confirm save before writing to YAML file
def confirm_save(customers):
    print("\nThe following data will be saved:")
    for customer in customers:
        print(customer)

    confirm = input("\nDo you want to proceed with saving the data? (y/n): ").strip().lower()
    return confirm == 'y'

# Main function to handle file input, manual input, and output
def main():
    try:
        print("Please choose an input method:")
        print("1. File Input (CSV/Excel)")
        print("2. Manual Input")
        choice = input("Enter your choice (1 or 2): ").strip()

        if choice == '1':
            customers = load_customer_file()
        elif choice == '2':
            customers = collect_manual_input()
        else:
            print("Invalid choice. Please enter 1 or 2.")
            return

        validated_customers = preview_and_edit(customers)

        if confirm_save(validated_customers):
            with open('customers.yml', 'w') as file:
                yaml.dump({'customers': validated_customers}, file)
            print("\nCustomer data successfully saved to customers.yml.")
        else:
            print("Save operation cancelled.")

    except Exception as e:
        logging.error(f"Error in main: {e}")
        print(f"An error occurred: {e}")

# Entry point of the script
if __name__ == "__main__":
    main()
