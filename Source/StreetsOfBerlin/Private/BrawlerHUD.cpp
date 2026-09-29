#include "BrawlerHUD.h"

#include "BrawlerAssets.h"
#include "BrawlerEnemy.h"
#include "BrawlerGameMode.h"
#include "BrawlerPlayer.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	const FLinearColor Ink(0.02f, 0.015f, 0.03f, 1.f);
	const FLinearColor Yellow(1.f, 0.78f, 0.1f, 1.f);
	const FLinearColor Green(0.3f, 0.9f, 0.35f, 1.f);
	const FLinearColor RedBar(0.95f, 0.2f, 0.2f, 1.f);
	const FLinearColor White(1.f, 1.f, 1.f, 1.f);
	const FLinearColor Pink(1.f, 0.25f, 0.5f, 1.f);
}

void ABrawlerHUD::Rect(float X, float Y, float W, float H, const FLinearColor& Color)
{
	DrawRect(Color, OX + X * S, OY + Y * S, W * S, H * S);
}

void ABrawlerHUD::Text(const FString& Str, float X, float Y, float Scale, const FLinearColor& Color, bool bCenter, bool bRight)
{
	UFont* Font = GEngine ? GEngine->GetLargeFont() : nullptr;
	float W = 0.f, H = 0.f;
	GetTextSize(Str, W, H, Font, Scale * S);
	float PX = OX + X * S;
	if (bCenter)
	{
		PX -= W * 0.5f;
	}
	else if (bRight)
	{
		PX -= W;
	}
	const float PY = OY + Y * S;
	// Kontur fuer Lesbarkeit
	const float O = FMath::Max(1.f, 2.f * S);
	for (const FVector2D& D : { FVector2D(-O, 0.f), FVector2D(O, 0.f), FVector2D(0.f, -O), FVector2D(0.f, O), FVector2D(O, O) })
	{
		DrawText(Str, Ink, PX + D.X, PY + D.Y, Font, Scale * S);
	}
	DrawText(Str, Color, PX, PY, Font, Scale * S);
}

void ABrawlerHUD::Tex(UTexture2D* Texture, float X, float Y, float W, float H, float Alpha)
{
	if (Texture)
	{
		DrawTexture(Texture, OX + X * S, OY + Y * S, W * S, H * S, 0.f, 0.f, 1.f, 1.f, FLinearColor(1.f, 1.f, 1.f, Alpha));
	}
}

void ABrawlerHUD::Bar(float X, float Y, float W, float H, float Value, float Recoverable, const FLinearColor& Color, bool bRightToLeft)
{
	Rect(X - 4.f, Y - 4.f, W + 8.f, H + 8.f, Ink);
	Rect(X, Y, W, H, FLinearColor(0.18f, 0.12f, 0.16f, 1.f));
	const float V = FMath::Clamp(Value, 0.f, 1.f);
	const float R = FMath::Clamp(Value + Recoverable, 0.f, 1.f);
	if (bRightToLeft)
	{
		Rect(X + W * (1.f - R), Y, W * R, H, Green);
		Rect(X + W * (1.f - V), Y, W * V, H, Color);
	}
	else
	{
		Rect(X, Y, W * R, H, Green);
		Rect(X, Y, W * V, H, Color);
	}
	// Glanzlinie
	Rect(X, Y + 2.f, W, 3.f, FLinearColor(1.f, 1.f, 1.f, 0.25f));
}

void ABrawlerHUD::FighterPanel(ABrawlerFighter* Fighter, bool bRightSide, float Recoverable)
{
	UBrawlerAssets* Assets = UBrawlerAssets::Get(this);
	UTexture2D* Portrait = Assets ? Assets->GetTexture(TEXT("UI"), TEXT("Portrait_") + Fighter->SpriteSet) : nullptr;

	const float PortraitSize = 96.f;
	const float BarW = 400.f;
	const float PX = bRightSide ? 1600.f - 24.f - PortraitSize : 24.f;
	Rect(PX - 4.f, 14.f, PortraitSize + 8.f, PortraitSize + 8.f, Ink);
	Rect(PX, 18.f, PortraitSize, PortraitSize, bRightSide ? FLinearColor(0.35f, 0.1f, 0.15f, 1.f) : FLinearColor(0.1f, 0.2f, 0.4f, 1.f));
	Tex(Portrait, PX, 18.f, PortraitSize, PortraitSize);

	const float BX = bRightSide ? PX - 16.f - BarW : PX + PortraitSize + 16.f;
	Text(Fighter->DisplayName, bRightSide ? BX + BarW : BX, 16.f, 1.1f, White, false, bRightSide);
	const float HealthFrac = Fighter->Health / FMath::Max(1.f, Fighter->MaxHealth);
	Bar(BX, 52.f, BarW, 22.f, HealthFrac, Recoverable / FMath::Max(1.f, Fighter->MaxHealth), bRightSide ? RedBar : Yellow, bRightSide);
}

void ABrawlerHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas)
	{
		return;
	}

	S = FMath::Min(Canvas->ClipX / 1600.f, Canvas->ClipY / 900.f);
	OX = (Canvas->ClipX - 1600.f * S) * 0.5f;
	OY = (Canvas->ClipY - 900.f * S) * 0.5f;

	ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	if (!GM)
	{
		return;
	}
	UBrawlerAssets* Assets = UBrawlerAssets::Get(this);
	const float T = GM->GetFlowTime();
	const bool bBlink = FMath::Fmod(GetWorld()->GetRealTimeSeconds(), 0.8f) < 0.5f;

	if (GM->GetFlow() == EBrawlerFlow::Title)
	{
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, 0.55f));
		UTexture2D* Logo = Assets ? Assets->GetTexture(TEXT("UI"), TEXT("UI_Logo")) : nullptr;
		if (Logo)
		{
			Tex(Logo, 250.f, 120.f, 1100.f, 300.f);
		}
		else
		{
			Text(TEXT("STREETS OF BERLIN"), 800.f, 220.f, 3.f, Yellow, true);
		}
		if (bBlink)
		{
			Text(TEXT("DRÜCKE ENTER / START"), 800.f, 500.f, 1.6f, White, true);
		}
		Text(TEXT("Laufen: WASD / Pfeile / Stick     Schlag: J / X     Sprung: K / A"), 800.f, 640.f, 0.9f, White, true);
		Text(TEXT("Spezial: L / Y (kostet Energie)     Rückschlag: I / B     Pause: Enter / Start"), 800.f, 680.f, 0.9f, White, true);
		Text(TEXT("In Gegner hineinlaufen = Griff  ->  Schlag = Knie,  weg + Schlag = Wurf"), 800.f, 720.f, 0.9f, White, true);
		return;
	}

	// --- Spieler-Panel -----------------------------------------------------
	if (ABrawlerPlayer* Player = GM->GetPlayer())
	{
		FighterPanel(Player, false, Player->GetRecoverableHealth());
		Text(FString::Printf(TEXT("x%d"), FMath::Max(0, GM->GetLives() - 1)), 30.f, 118.f, 1.1f, Yellow);
		Text(FString::Printf(TEXT("%07d"), GM->GetScore()), 136.f, 84.f, 1.1f, White);
	}

	// --- Gegner-Panel ------------------------------------------------------
	ABrawlerFighter* Enemy = GM->GetLastHitEnemy();
	if (Enemy && (GM->GetLastHitEnemyTimer() > 0.f || (GM->IsBossFight() && Cast<ABrawlerEnemy>(Enemy) && Cast<ABrawlerEnemy>(Enemy)->IsBoss())))
	{
		FighterPanel(Enemy, true, 0.f);
	}

	// --- Combo ---------------------------------------------------------------
	if (GM->GetComboHits() >= 2 && GM->GetComboTimer() > 0.f)
	{
		const float Pop = 1.f + FMath::Clamp(GM->GetComboTimer() - 1.2f, 0.f, 0.2f) * 2.f;
		Text(FString::Printf(TEXT("%d"), GM->GetComboHits()), 40.f, 170.f, 2.6f * Pop, Yellow);
		Text(TEXT("HITS"), 40.f, 240.f, 1.1f, White);
	}

	// --- GO-Pfeil ------------------------------------------------------------
	if (GM->GetGoArrowTimer() > 0.f && bBlink)
	{
		UTexture2D* Go = Assets ? Assets->GetTexture(TEXT("UI"), TEXT("UI_Go")) : nullptr;
		if (Go)
		{
			Tex(Go, 1360.f, 360.f, 200.f, 110.f);
		}
		else
		{
			Text(TEXT("GO ->"), 1450.f, 380.f, 2.f, Yellow, true);
		}
	}

	// --- Ablauf-Texte --------------------------------------------------------
	switch (GM->GetFlow())
	{
	case EBrawlerFlow::Intro:
		Text(TEXT("STAGE 1"), 800.f, 330.f, 2.2f, Yellow, true);
		Text(TEXT("KREUZBERG BEI NACHT"), 800.f, 400.f, 1.6f, White, true);
		break;
	case EBrawlerFlow::StageClear:
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, FMath::Clamp(T * 0.3f, 0.f, 0.5f)));
		Text(TEXT("STAGE CLEAR!"), 800.f, 300.f, 3.f, Yellow, true);
		Text(FString::Printf(TEXT("PUNKTE: %d"), GM->GetScore()), 800.f, 420.f, 1.6f, White, true);
		if (T > 2.f && bBlink)
		{
			Text(TEXT("ENTER / START"), 800.f, 520.f, 1.2f, White, true);
		}
		break;
	case EBrawlerFlow::GameOver:
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, FMath::Clamp(T * 0.4f, 0.f, 0.65f)));
		Text(TEXT("GAME OVER"), 800.f, 320.f, 3.2f, Pink, true);
		if (T > 1.5f && bBlink)
		{
			Text(TEXT("ENTER / START: NOCHMAL"), 800.f, 470.f, 1.2f, White, true);
		}
		break;
	default:
		break;
	}

	if (UGameplayStatics::IsGamePaused(this))
	{
		Rect(0.f, 0.f, 1600.f, 900.f, FLinearColor(0.f, 0.f, 0.f, 0.5f));
		Text(TEXT("PAUSE"), 800.f, 400.f, 2.6f, White, true);
	}
}
