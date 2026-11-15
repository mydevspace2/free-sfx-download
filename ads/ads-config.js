/* =====================================================================
   ADSTERRA AD CODES - the ONLY file you need to edit to turn ads on.
   ---------------------------------------------------------------------
   1. In Adsterra, create a "Banner" ad unit for each size below and copy
      its code (the <script>atOptions ...</script><script src=".../invoke.js"></script> block).
   2. Paste it between the backticks ` ` of the matching slot.
   3. For Popunder or Social Bar codes, paste them into "global".
   4. Commit/push. Every page picks the codes up automatically.
   Empty slots stay invisible (no blank boxes).

   Slots on every page:
     header    -> under the top menu       (728x90; mobile: 320x50)
     incontent -> inside the sound grid    (300x250)  [home + category pages]
     footer    -> above the footer         (728x90; mobile: 300x250)
   ===================================================================== */
window.SFX_ADS = {
  enabled: true,
  slots: {
    header: {
      width: 728, height: 90,
      code: ``,
      mobile: { width: 320, height: 50, code: `` }
    },
    incontent: {
      width: 300, height: 250,
      code: ``
    },
    footer: {
      width: 728, height: 90,
      code: ``,
      mobile: { width: 300, height: 250, code: `` }
    }
  },
  // Popunder / Social Bar code (loads once per page, outside any slot):
  global: ``
};
