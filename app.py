--- app.py (previous)
+++ app.py (updated)
@@ -106,20 +106,24 @@
     pace = (len(f_df) / 400) * 30.44
     overlap = (len(f_df[f_df['Cat_Count'] > 1]) / len(f_df) * 100) if len(f_df) > 0 else 0
     
+    # GLOBAL INVESTIGATIVE DIAGNOSTIC BOX
+    st.markdown(f"""
+    <div style="background: rgba(128, 128, 128, 0.05); padding: 15px; border-radius: 10px; margin-top: 15px; border: 1px solid rgba(128, 128, 128, 0.1);">
+        <p style="margin:0; font-size:0.85rem; opacity:0.85; line-height:1.4;">
+            🔍 <b>Investigative Diagnostic:</b> Metrics and charts sync to your search and/or filters. 
+            Use the sidebar to compare the <b>Velocity</b> and <b>Complexity</b> of specific democracy dismantling efforts, and isolate specific threats.
+        </p>
+    </div>
+    """, unsafe_allow_html=True)
+
     st.divider()
     st.subheader("◈ Institutional Health Diagnostic")
     st.markdown(f"""
-    <div style="background: rgba(128, 128, 128, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid rgba(128, 128, 128, 0.1);">
-        <p style="margin:0; font-size:0.85rem; opacity:0.85; line-height:1.4;">
-            🔍 <b>Investigative Diagnostic:</b> Metrics sync to your search and/or filters. 
-            Use the sidebar to compare the <b>Velocity</b> and <b>Complexity</b> of specific democracy dismantling efforts, and isolate specific threats.
-        </p>
-    </div>
     <div class="hero-container">
