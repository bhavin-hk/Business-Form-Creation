from flask import Flask, request, send_file, render_template_string
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# --- FRONTEND: SPLIT-SCREEN UI WITH MULTIPLE PRODUCTS ---
@app.route('/')
def home():
    html_page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>JHOM EXIM Pro Quote Generator</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e9ecef; margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }
            
            /* Left Side */
            .form-section { width: 45%; background: white; padding: 30px; overflow-y: auto; box-shadow: 2px 0 10px rgba(0,0,0,0.1); z-index: 10; }
            .form-section h2 { margin-top: 0; color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; font-size: 13px; }
            input[type="text"], input[type="number"], select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            input[readonly] { background-color: #e9ecef; color: #6c757d; cursor: not-allowed; font-weight: bold;}
            .row { display: flex; gap: 15px; }
            .row .form-group { flex: 1; }
            
            /* Product Box Styling */
            .product-block { background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 6px; margin-bottom: 20px; position: relative; }
            .product-block h4 { margin-top: 0; margin-bottom: 15px; color: #0056b3; }
            .remove-btn { position: absolute; top: 15px; right: 15px; background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 12px;}
            .add-product-btn { background: #28a745; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; cursor: pointer; font-weight: bold; margin-bottom: 20px;}
            
            .submit-btn { width: 100%; padding: 15px; background: #0056b3; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; margin-top: 20px; font-weight: bold; transition: 0.2s; }
            .submit-btn:hover { background: #004494; }

            /* Right Side */
            .preview-section { width: 55%; background: #525659; display: flex; justify-content: center; align-items: flex-start; overflow-y: auto; padding: 40px; }
            .paper { background: white; width: 612px; min-height: 792px; padding: 50px; box-sizing: border-box; box-shadow: 0 10px 20px rgba(0,0,0,0.3); font-family: Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.5; color: #000; }
            .paper hr { border: 0; border-top: 1.5px solid #000; margin: 25px 0; }
            .paper h3 { font-size: 18px; margin-bottom: 15px; }
            .paper ul { list-style-type: none; padding-left: 20px; margin: 10px 0; }
            .paper ul li { position: relative; margin-bottom: 8px; }
            .paper ul li::before { content: "•"; position: absolute; left: -15px; }
            .highlight { background-color: #e8f0fe; padding: 0 2px; border-radius: 2px; }
        </style>
    </head>
    <body>

        <div class="form-section">
            <h2>📝 Generate Quotation</h2>
            <form action="/generate-pdf" method="POST">
                
                <div id="products-container"></div>
                <button type="button" class="add-product-btn" onclick="addProduct()">+ Add Another Product</button>

                <hr style="border: 1px solid #eee; margin: 20px 0;">

                <div class="row">
                    <div class="form-group">
                        <label>Price Term</label>
                        <select id="price_term" name="price_term" onchange="updatePreview()">
                            <option value="FOB">FOB</option>
                            <option value="CIF">CIF</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Grand Total Price ($)</label>
                        <input type="text" id="grand_total" name="grand_total" value="0.00" readonly>
                    </div>
                </div>

                <div class="row">
                    <div class="form-group">
                        <label>Advance Payment %</label>
                        <input type="number" id="advance_pct" name="advance_pct" value="60" oninput="calculateMath()" required>
                    </div>
                    <div class="form-group">
                        <label>Balance Payment %</label>
                        <input type="number" id="balance_pct" name="balance_pct" value="40" readonly required>
                    </div>
                </div>

                <div class="row">
                    <div class="form-group">
                        <label>Delivery Mode</label>
                        <select id="delivery_mode" name="delivery_mode" onchange="updatePreview()">
                            <option value="By Sea">By Sea</option>
                            <option value="By Air">By Air</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Timeline (Days)</label>
                        <input type="text" id="timeline" name="timeline" value="30-45 days" oninput="updatePreview()" required>
                    </div>
                </div>

                <button type="submit" class="submit-btn">🚀 Export Finished PDF</button>
            </form>
        </div>

        <div class="preview-section">
            <div class="paper">
                <strong>Greetings from JHOM EXIM WORLDWIDE LLP!</strong><br><br>
                We are pleased to offer you a quotation for the export of premium-quality products, as per your interest. Please find the detailed proposal below.
                <hr>
                
                <h3>Product Details</h3>
                <div id="preview_products_list"></div> <hr>

                <h3>Price Terms (<span class="highlight" id="prev_price_term">FOB</span>)</h3>
                <ul id="preview_prices_list"></ul> <hr>

                <h3>Payment Terms</h3>
                <ul>
                    <li><span class="highlight" id="prev_advance">60</span>% Advance of the total <span id="prev_price_term_2">FOB</span> Value upon order confirmation</li>
                    <li><span class="highlight" id="prev_balance">40</span>% Balance under Irrevocable Letter of Credit (LC) at sight</li>
                </ul>
                <hr>

                <h3>Estimated Delivery Timeline</h3>
                <ul>
                    <li><span class="highlight" id="prev_delivery_mode">By Sea</span>: <span class="highlight" id="prev_timeline">30-45 days</span> (depending on vessel schedule & clearance)</li>
                </ul>
                <br>
                We look forward to building a strong and successful business relationship with you.
            </div>
        </div>

        <script>
            let productCount = 0;

            // Function to add a new product block to the form
            function addProduct() {
                productCount++;
                const container = document.getElementById("products-container");
                const div = document.createElement("div");
                div.className = "product-block";
                div.id = `product_block_${productCount}`;
                
                div.innerHTML = `
                    <h4>📦 Product ${productCount}</h4>
                    <button type="button" class="remove-btn" onclick="removeProduct('${div.id}')">X Remove</button>
                    
                    <div class="form-group">
                        <label>Product Name</label>
                        <input type="text" name="product_name" class="p_name" value="Cardamom" oninput="updatePreview()" required>
                    </div>
                    <div class="row">
                        <div class="form-group"><label>Quantity</label><input type="text" name="quantity" class="p_qty" value="12 MT" oninput="updatePreview()" required></div>
                        <div class="form-group"><label>Packaging</label><input type="text" name="packaging" class="p_pkg" value="10 kg" oninput="updatePreview()" required></div>
                    </div>
                    <div class="row">
                        <div class="form-group"><label>Grade</label><input type="text" name="grade" class="p_grade" value="Export Quality" oninput="updatePreview()" required></div>
                        <div class="form-group"><label>Origin</label><input type="text" name="origin" class="p_origin" value="India" oninput="updatePreview()" required></div>
                    </div>
                    <div class="form-group">
                        <label>Price for this Product ($)</label>
                        <input type="number" name="price" class="p_price" value="359300" oninput="updatePreview()" required>
                    </div>
                `;
                container.appendChild(div);
                updatePreview();
            }

            // Function to remove a product block
            function removeProduct(blockId) {
                document.getElementById(blockId).remove();
                updatePreview();
            }

            // Central engine to read all data and update preview
            function updatePreview() {
                const blocks = document.querySelectorAll(".product-block");
                let productsHTML = "";
                let pricesHTML = "";
                let grandTotal = 0;

                blocks.forEach((block, index) => {
                    const name = block.querySelector(".p_name").value || "...";
                    const qty = block.querySelector(".p_qty").value || "...";
                    const pkg = block.querySelector(".p_pkg").value || "...";
                    const grade = block.querySelector(".p_grade").value || "...";
                    const origin = block.querySelector(".p_origin").value || "...";
                    const price = parseFloat(block.querySelector(".p_price").value) || 0;

                    grandTotal += price;

                    // Build Preview Product Section
                    productsHTML += `
                        <strong>${index + 1}. <span class="highlight">${name}</span></strong>
                        <ul>
                            <li>Quantity: <span class="highlight">${qty}</span></li>
                            <li>Packaging: <span class="highlight">${pkg}</span></li>
                            <li>Grade: <span class="highlight">${grade}</span></li>
                            <li>Origin: <span class="highlight">${origin}</span></li>
                        </ul>
                    `;

                    // Build Preview Price Section
                    pricesHTML += `<li><span class="highlight">${name}</span>: $${price.toLocaleString('en-US', {minimumFractionDigits: 2})}</li>`;
                });

                // Set Grand Total Price
                document.getElementById("grand_total").value = grandTotal.toLocaleString('en-US', {minimumFractionDigits: 2});
                
                // Inject into Paper
                document.getElementById("preview_products_list").innerHTML = productsHTML;
                document.getElementById("preview_prices_list").innerHTML = pricesHTML;

                // Update standard fields
                const pTerm = document.getElementById("price_term").value;
                document.getElementById("prev_price_term").innerText = pTerm;
                document.getElementById("prev_price_term_2").innerText = pTerm;
                document.getElementById("prev_delivery_mode").innerText = document.getElementById("delivery_mode").value;
                document.getElementById("prev_timeline").innerText = document.getElementById("timeline").value;
                
                calculateMath();
            }

            // Math logic
            function calculateMath() {
                let advance = document.getElementById("advance_pct").value;
                if (advance !== "" && advance >= 0 && advance <= 100) {
                    document.getElementById("balance_pct").value = 100 - advance;
                } else if (advance > 100) {
                    document.getElementById("advance_pct").value = 100;
                    document.getElementById("balance_pct").value = 0;
                }
                document.getElementById("prev_advance").innerText = document.getElementById("advance_pct").value || "0";
                document.getElementById("prev_balance").innerText = document.getElementById("balance_pct").value || "100";
            }

            // Start with 1 default product
            window.onload = function() {
                addProduct();
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_page)

# --- BACKEND: SMART PAGINATION GENERATOR ---
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    data = request.form
    
    # Because we used the same name for all products, Flask groups them into Lists!
    names = data.getlist('product_name')
    quantities = data.getlist('quantity')
    packagings = data.getlist('packaging')
    grades = data.getlist('grade')
    origins = data.getlist('origin')
    prices = data.getlist('price')

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    left_margin = 50
    y = 730

    # HELPER FUNCTION: Check if we need to add a new page
    def check_page_break(current_y, space_needed):
        if current_y - space_needed < 50:
            c.showPage() # Create new page
            c.setFont("Helvetica", 11) # Reapply standard font
            return 750 # Reset Y to the top of the new page
        return current_y

    # Header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(left_margin, y, "Greetings from JHOM EXIM WORLDWIDE LLP!")
    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(left_margin, y, "We are pleased to offer you a quotation for the export of premium-quality products.")
    y -= 15
    c.drawString(left_margin, y, "Please find the detailed proposal below.")
    y -= 25
    c.setLineWidth(1)
    c.line(left_margin, y, 560, y)
    y -= 30

    # Product Details Loop
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left_margin, y, "Product Details")
    y -= 25

    bullet_indent = 70
    
    for i in range(len(names)):
        y = check_page_break(y, 100) # Ensure we have enough room for this product block
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_margin, y, f"{i+1}. {names[i]}")
        y -= 20
        
        c.setFont("Helvetica", 11)
        c.drawString(bullet_indent, y, f"•  Quantity: {quantities[i]}")
        y -= 15
        c.drawString(bullet_indent, y, f"•  Packaging: {packagings[i]}")
        y -= 15
        c.drawString(bullet_indent, y, f"•  Grade: {grades[i]}")
        y -= 15
        c.drawString(bullet_indent, y, f"•  Origin: {origins[i]}")
        y -= 25

    c.line(left_margin, y, 560, y)
    y -= 30

    # Price Terms Loop
    y = check_page_break(y, 80)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left_margin, y, f"Price Terms ({data.get('price_term')})")
    y -= 25
    
    c.setFont("Helvetica", 11)
    for i in range(len(names)):
        y = check_page_break(y, 20)
        formatted_price = "{:,.2f}".format(float(prices[i]))
        c.drawString(bullet_indent, y, f"•  {names[i]}: ${formatted_price}")
        y -= 15
        
    y -= 10
    c.line(left_margin, y, 560, y)
    y -= 30

    # Payment Terms
    y = check_page_break(y, 80)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left_margin, y, "Payment Terms") 
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(bullet_indent, y, f"•  {data.get('advance_pct')}% Advance of the total {data.get('price_term')} Value upon order confirmation")
    y -= 15
    c.drawString(bullet_indent, y, f"•  {data.get('balance_pct')}% Balance under Irrevocable Letter of Credit (LC) at sight")
    y -= 25
    c.line(left_margin, y, 560, y)
    y -= 30

    # Delivery Timeline
    y = check_page_break(y, 60)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left_margin, y, "Estimated Delivery Timeline")
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(bullet_indent, y, f"•  {data.get('delivery_mode')}: {data.get('timeline')} (depending on vessel schedule & clearance)")
    y -= 40

    y = check_page_break(y, 30)
    c.drawString(left_margin, y, "We look forward to building a strong and successful business relationship with you.")

    c.save()
    buffer.seek(0)
    
    # Save file with first product name
    filename = f"Quotation_{names[0]}.pdf".replace(" ", "_")
    return send_file(buffer, download_name=filename, as_attachment=True, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)