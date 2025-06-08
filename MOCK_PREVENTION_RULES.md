
# 🛡️ MOCK DATA CONTAMINATION PREVENTION RULES

## ❌ NEVER ALLOW THESE PATTERNS:

1. **Fake Transaction Hashes**
   - ❌ `0x` + 64 repeated characters (0xaaaa..., 0x1111..., etc.)
   - ✅ Use real blockchain transaction hashes only

2. **Simulation Delays**
   - ❌ `await asyncio.sleep(0.1)` for fake execution timing
   - ✅ Real blockchain calls only

3. **Safety Mode Messages**
   - ❌ "SAFETY MODE ACTIVE"
   - ❌ "Would trade", "Would execute", "Would use"
   - ✅ Real execution messages only

4. **Mock Environment Variables**
   - ❌ `ENABLE_REAL_TRANSACTIONS=false` (default)
   - ✅ `ENABLE_REAL_TRANSACTIONS=true` (production)

## ✅ PRODUCTION MODE REQUIREMENTS:

1. **Environment Variables**
   ```bash
   export ENABLE_REAL_TRANSACTIONS=true
   ```

2. **Real Transaction Execution**
   - All trades must use actual blockchain calls
   - No simulation or mock transaction hashes
   - Real gas estimation and execution

3. **Error Handling**
   - Handle real blockchain errors
   - No fake success/failure responses

## 🔧 ENFORCEMENT:

Run these commands regularly:
```bash
python mock_data_exterminator.py      # Scan for contamination
python fix_mock_data_contamination.py # Fix any issues found
python verify_real_execution.py       # Verify fixes worked
```

## 🚨 RED FLAGS:

If you see ANY of these, the system is contaminated:
- Transaction hashes like 0xaaaa... or 0x1111...
- "Would trade" or "SAFETY MODE" messages
- asyncio.sleep() calls in execution code
- ENABLE_REAL_TRANSACTIONS=false

## 💰 THE GOAL:

REAL BLOCKCHAIN EXECUTION = REAL PROFITS
NO MOCK DATA = NO BLOCKED GREEN
