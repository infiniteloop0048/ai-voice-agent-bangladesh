<?php

use App\Http\Controllers\VoiceWebhookController;
use Illuminate\Support\Facades\Route;

Route::post('/webhooks/voice', [VoiceWebhookController::class, 'handle']);
