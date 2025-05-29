from flask import Blueprint, request, jsonify
from middlewares.auth import token_required
from extensions import db
from models.device import DeviceTransaction  # Adjust import based on your structure
import pandas as pd
from datetime import datetime


device_transaction_bp = Blueprint('device_transaction', __name__)

from flask import jsonify, request
from datetime import datetime
import pandas as pd
import math

@device_transaction_bp.route('/upload-device-transaction', methods=['POST'])
@token_required(roles=['admin'])
def upload_device_transaction():
    print("Upload endpoint hit")  # Debug log
    if 'file' not in request.files:
        print("No file part in request")  # Debug log
        return jsonify({'success': False, 'message': 'No file part in the request'}), 400

    file = request.files['file']
    print(f"File received: {file.filename}")  # Debug log

    if file.filename == '':
        print("Empty filename")  # Debug log
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    try:
        if file.filename.endswith('.csv'):
            print("Reading CSV file")  # Debug log
            df = pd.read_csv(file)
        elif file.filename.endswith('.xlsx'):
            print("Reading Excel file")  # Debug log
            df = pd.read_excel(file, engine='openpyxl')
        else:
            print(f"Unsupported file format: {file.filename}")  # Debug log
            return jsonify({
                'success': False,
                'message': 'Unsupported file format. Only CSV and Excel are allowed.'
            }), 400

        print(f"File read successfully. Shape: {df.shape}")
        print(f"First 2 rows:\n{df.head(2)}")

        if df.empty:
            return jsonify({'success': False, 'message': 'File is empty'}), 400

        # Clean string columns
        df = df.apply(lambda x: x.astype(str).str.strip() if x.dtype == 'object' else x)

        success_count = 0
        error_rows = []

        for index, row in df.iterrows():
            try:
                print(f"\nProcessing row {index}: {row.to_dict()}")

                # Extract and clean values
                device_srno = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                model_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
                sku_id = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
                if sku_id and sku_id.lower() == 'nan':
                    sku_id = None

                order_id = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None

                in_out = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
                if in_out.lower() == 'nan':
                    in_out = ''

                try:
                    price = float(row.iloc[5]) if pd.notna(row.iloc[5]) else None
                except (ValueError, TypeError):
                    price = None

                remarks = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else None

                print(f"Extracted values - SRNO: {device_srno}, Model: {model_name}, IN_OUT: {in_out}")

                # Mandatory validation - skip rows missing any required field
                if not device_srno or not model_name or not in_out:
                    error_msg = (
                        f"Missing mandatory field - SRNO: {device_srno or 'empty'}, "
                        f"Model: {model_name or 'empty'}, IN_OUT: {in_out or 'empty'}"
                    )
                    print(error_msg)
                    error_rows.append({
                        'row': index + 1,
                        'error': error_msg
                    })
                    continue

                # Save record
                transaction = DeviceTransaction(
                    device_srno=device_srno,
                    model_name=model_name,
                    sku_id=sku_id,
                    order_id=order_id,
                    in_out=in_out,
                    price=price,
                    remarks=remarks,
                    create_date=datetime.now().date()
                )
                db.session.add(transaction)
                success_count += 1
                print(f"Row {index} added successfully")

            except Exception as e:
                error_msg = f"Error processing row {index}: {str(e)}"
                print(error_msg)
                error_rows.append({
                    'row': index + 1,
                    'error': str(e)
                })

        db.session.commit()
        print(f"Commit successful. {success_count} rows processed")

        return jsonify({
            'success': True,
            'message': f'Successfully processed {success_count} rows',
            'failed_rows': error_rows,
            'failed_count': len(error_rows),
            'total_rows': len(df)
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Global error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Processing error: {str(e)}'
        }), 500



    



@device_transaction_bp.route('/search-device', methods=['POST'])
@token_required(roles=['admin', 'customer'])  # Adjust roles as needed
def search_device():
    data = request.get_json()
    search_term = data.get('search_term')
    
    if not search_term:
        return jsonify({'success': False, 'message': 'Search term required'}), 400

    try:
        # Search by either device_srno or sku_id
        transactions = DeviceTransaction.query.filter(
            (DeviceTransaction.device_srno == search_term) | 
            (DeviceTransaction.sku_id == search_term)
        ).order_by(DeviceTransaction.create_date).all()

        if not transactions:
            return jsonify({'success': False, 'message': 'No transactions found'}), 404

        # Analyze transactions
        in_trans = next((t for t in transactions if t.in_out == 1), None)
        out_trans = next((t for t in transactions if t.in_out == 2), None)
        return_trans = next((t for t in transactions if t.in_out == 3), None)

        response = {
            'device_srno': transactions[0].device_srno,
            'sku_id': transactions[0].sku_id,
            'model_name': transactions[0].model_name
        }

        if return_trans:
            response['status'] = 'RETURN'
            response['message'] = 'Return transaction'
            response['return_details'] = {
                'date': return_trans.create_date.isoformat(),
                'remarks': return_trans.remarks
            }
        elif in_trans and out_trans:
            profit = float(out_trans.price) - float(in_trans.price)
            response['status'] = 'SOLD'
            response['profit'] = profit
            response['in_price'] = float(in_trans.price)
            response['out_price'] = float(out_trans.price)
            response['in_date'] = in_trans.create_date.isoformat()
            response['out_date'] = out_trans.create_date.isoformat()
        elif in_trans and not out_trans:
            response['status'] = 'IN_STOCK'
            response['message'] = 'No OUT transaction found'
            response['in_price'] = float(in_trans.price)
            response['in_date'] = in_trans.create_date.isoformat()
        elif out_trans and not in_trans:
            response['status'] = 'SOLD_WITHOUT_IN'
            response['message'] = 'No IN transaction found'
            response['out_price'] = float(out_trans.price)
            response['out_date'] = out_trans.create_date.isoformat()
        else:
            response['status'] = 'UNKNOWN'
            response['message'] = 'Unexpected transaction combination'

        return jsonify({'success': True, 'data': response})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

    

@device_transaction_bp.route('/get-all-device-transactions', methods=['GET'])
def get_all_device_transactions():
    try:
        device_srno = request.args.get('device_srno')
        
        if device_srno:
            # Search for specific device
            transactions = DeviceTransaction.query.filter(
                DeviceTransaction.device_srno == device_srno
            ).order_by(DeviceTransaction.create_date.desc()).all()
        else:
            # Get all devices if no srno specified
            transactions = DeviceTransaction.query.order_by(
                DeviceTransaction.create_date.desc()
            ).all()

        if not transactions:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No transactions found' if device_srno else 'No devices in database'
            })

        # Serialize the transactions
        data = []
        for t in transactions:
            data.append({
                'id': t.auto_id,
                'device_srno': t.device_srno,
                'model_name': t.model_name,
                'sku_id': t.sku_id,
                'order_id': t.order_id,
                'in_out': t.in_out,
                'create_date': t.create_date.isoformat() if t.create_date else None,
                'price': float(t.price) if t.price else None,
                'remarks': t.remarks
            })

        return jsonify({
            'success': True,
            'data': data,
            'message': f'Found {len(data)} transactions'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

from zoneinfo import ZoneInfo

@device_transaction_bp.route('/add-device', methods=['POST'])
def add_device():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('device_srno') or not data.get('model_name'):
            return jsonify({'success': False, 'message': 'Device SR No and Name are required'}), 400
        
        # Create new device transaction
        new_device = DeviceTransaction(
            device_srno=data['device_srno'],
            model_name=data['model_name'],
            sku_id=data.get('sku_id', ''),
            order_id=data.get('order_id', ''),
            in_out=int(data.get('in_out', 1)),
            price=float(data['price']) if 'price' in data else None,
            remarks=data.get('remarks', ''),
            create_date=datetime.now(tz=ZoneInfo('Asia/Kolkata'))
        )
        
        db.session.add(new_device)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Device added successfully',
            'data': {
                'device_srno': new_device.device_srno,
                'model_name': new_device.model_name
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
