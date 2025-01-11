import pandas as pd
import yaml
import os
import ipaddress
import logging
from tqdm import tqdm
import re
from datetime import datetime

# Set up logging to track the script's actions and errors
logging.basicConfig(
    filename='customer_processing.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Service-to-Tag mapping
tag_mapping = {
    '20022': 'MFT_Financial',
    '20024': 'MFT_Healthcare',
    # Add more mappings as needed
}

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

# Load customer data from file without headers
def load_customer_file():
    while True:
        file_path = input("Enter the path to the file (CSV or Excel, no headers required): ").strip()
        if os.path.exists(file_path):
            if file_path.endswith('.csv'):
                customers = []
                with open(file_path, 'r') as file:
                    for line in file:
                        fields = line.strip().split(',')
                        if len(fields) < 3:
                            print("Error: Each row must have at least CustomerName, CustomerIPAddress, and IPSubnetMask.")
                            continue

                        name = fields[0].strip()
                        ip_address = fields[1].strip()
                        subnet_mask = fields[2].strip()
                        service = fields[3].strip() if len(fields) > 3 else ''

                        # Validate IP address and subnet mask
                        if not validate_ip_address(ip_address):
                            continue
                        if not validate_subnet_mask(subnet_mask):
                            continue

                        # Generate object name
                        object_name = generate_object_name(name, ip_address, subnet_mask)

                        # Map service to tag
                        tag = tag_mapping.get(service)
                        if not tag and service:
                            print(f"Warning: The tag for service '{service}' is undefined.")
                            tag = input("Please enter a tag for this service, or leave it blank to skip: ").strip()

                        customers.append({
                            'CustomerName': name,
                            'CustomerIPAddress': ip_address,
                            'IPSubnetMask': subnet_mask,
                            'Tags': [tag] if tag else [],
                            'ObjectName': object_name
                        })
                return customers
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, header=None)
                customers = []
                for row in df.itertuples(index=False):
                    if len(row) < 3:
                        print("Error: Each row must have at least CustomerName, CustomerIPAddress, and IPSubnetMask.")
                        continue

                    name, ip_address, subnet_mask = [str(value).strip() for value in row[:3]]
                    service = str(int(row[3])).strip() if len(row) > 3 and pd.notna(row[3]) else ''

                    # New IP and subnet validation with user prompts to correct invalid entries
                    while not validate_ip_address(ip_address):
                        print(f"Invalid IP address detected: {ip_address}")
                        ip_address = input("Please enter a valid IP Address: ").strip()

                   while not validate_subnet_mask(subnet_mask):
                       print(f"Invalid subnet mask detected: {subnet_mask}")
                       subnet_mask = input("Please enter a valid subnet mask (e.g., 255.255.255.0 or /24): ").strip()

                    # Generate object name
                    object_name = generate_object_name(name, ip_address, subnet_mask)

                    # Map service to tag
                    tag = tag_mapping.get(service)
                    if not tag and service:
                        print(f"Warning: The tag for service '{service}' is undefined.")
                        tag = input("Please enter a tag for this service, or leave it blank to skip: ").strip()

                    customers.append({
                        'CustomerName': name,
                        'CustomerIPAddress': ip_address,
                        'IPSubnetMask': subnet_mask,
                        'Tags': [tag] if tag else [],
                        'ObjectName': object_name
                    })
                return customers
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

        service = input("Enter Service (optional): ").strip()
        tag = tag_mapping.get(service)
        if not tag and service:
            print(f"Warning: The tag for service '{service}' is undefined.")
            tag = input("Please enter a tag for this service, or leave it blank to skip: ").strip()

        object_name = generate_object_name(name, ip_address, subnet_mask)

        customers.append({
            'CustomerName': name,
            'CustomerIPAddress': ip_address,
            'IPSubnetMask': subnet_mask,
            'Tags': [tag] if tag else [],
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
            new_service = input("Enter new Service (leave blank to keep current): ").strip()
            if new_service:
                new_tag = tag_mapping.get(new_service)
                if not new_tag:
                    print(f"Warning: The tag for service '{new_service}' is undefined.")
                    new_tag = input("Please enter a tag for this service, or leave it blank to skip: ").strip()
                customer['Tags'] = [new_tag] if new_tag else []
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

# Generate the YAML file name dynamically
def generate_yaml_filename(customers):
    first_customer_name = customers[0]['CustomerName'].replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%H%M%S")
    return f"customers_{first_customer_name}_{timestamp}.yml"

# Main function to handle file input, manual input, and output
def main():
    try:
        while True:
            print("Please choose an input method:")
            print("1. File Input (CSV or Excel)")
            print("2. Manual Input")
            choice = input("Enter your choice (1 or 2): ").strip()

            if choice == '1':
                customers = load_customer_file()
                break
            elif choice == '2':
                customers = collect_manual_input()
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")

        validated_customers = preview_and_edit(customers)

        if confirm_save(validated_customers):
            yaml_filename = generate_yaml_filename(validated_customers)
            with open(yaml_filename, 'w') as file:
                yaml.dump({'customers': validated_customers}, file)
            print(f"\nCustomer data successfully saved to {yaml_filename}.")
        else:
            print("Save operation cancelled.")

    except Exception as e:
        logging.error(f"Error in main: {e}")
        print(f"An error occurred: {e}")

# Entry point of the script
if __name__ == "__main__":
    main()
